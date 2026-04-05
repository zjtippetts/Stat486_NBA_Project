"""
Build the player-level supervised learning table: college features -> success_composite_v1.

College ``cbb_*`` columns on ``model_base_player_season.csv`` come from each player's
**most recent NCAA season** row (not the Sports Reference **Career** aggregate), built in
``src/data/run_data_pull.py`` / ``rebuild_model_base``.

Rows: tier D, entry cohort, non-null college_player_id, non-null target.
Complete-case on ``cbb_advanced_BPM`` (drop players missing college BPM on SR).

Non-college signals (no full re-scrape required):
  - ``nba_debut_age``: first NBA season start year minus birth year (``birthday`` + summary).
  - ``pos_is_SG`` … ``pos_is_C``, ``pos_is_UNK``: dummies from NBA ``Pos`` on the player's
    **earliest** deduped season row (same 2TM dedupe rule as outcomes). Only **PG, SG, SF, PF, C**
    (first token if hyphenated). **PG** is the reference level (all five dummies 0); **UNK** for
    missing or non-matching labels.

College advanced only for rates (no ``cbb_totals_*`` / ``cbb_per100_*`` in this table).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from src.analysis.career_outcomes import dedupe_nba_player_season, season_start_year

TARGET_COL: Final = "success_composite_v1"
BPM_COL: Final = "cbb_advanced_BPM"

# NBA rookie-season position (reference = PG).
POS_DUMMY_COLS: Final[tuple[str, ...]] = (
    "pos_is_SG",
    "pos_is_SF",
    "pos_is_PF",
    "pos_is_C",
    "pos_is_UNK",
)
DEMOGRAPHIC_FEATURE_COLS: Final[list[str]] = ["nba_debut_age", *POS_DUMMY_COLS]

CBB_ADVANCED_FEATURE_COLS: Final[list[str]] = [
    "cbb_advanced_PER",
    "cbb_advanced_BPM",
    "cbb_advanced_OBPM",
    "cbb_advanced_DBPM",
    "cbb_advanced_WS_40",
    "cbb_advanced_USGpct",
    "cbb_advanced_TSpct",
    "cbb_advanced_ASTpct",
    "cbb_advanced_TRBpct",
    "cbb_advanced_ORBpct",
    "cbb_advanced_DRBpct",
    "cbb_advanced_STLpct",
    "cbb_advanced_BLKpct",
    "cbb_advanced_TOVpct",
    "cbb_advanced_OWS",
    "cbb_advanced_DWS",
    "cbb_advanced_WS",
]


_VALID_POS: Final[frozenset[str]] = frozenset({"PG", "SG", "SF", "PF", "C"})


def _rookie_pos_code(pos: str | float) -> str:
    """Normalize BR ``Pos`` to **PG / SG / SF / PF / C** or **UNK** (first token if hyphenated)."""
    if pos is None or (isinstance(pos, float) and np.isnan(pos)):
        return "UNK"
    p = str(pos).upper().strip()
    if not p or p == "NAN":
        return "UNK"
    first = re.split(r"[-/,]", p)[0].strip()
    if first not in _VALID_POS:
        return "UNK"
    return first


def _rookie_season_pos_from_model_base(mb: pd.DataFrame) -> pd.DataFrame:
    """One row per ``nba_player_id``: ``Pos`` on earliest season (deduped)."""
    d = dedupe_nba_player_season(mb)
    if d.empty or "Pos" not in d.columns:
        return pd.DataFrame(columns=["nba_player_id", "_pos_group"])
    d = d.copy()
    d["_y0"] = d["Season"].map(season_start_year)
    d = d[d["_y0"] >= 1990]
    if d.empty:
        return pd.DataFrame(columns=["nba_player_id", "_pos_group"])
    idx = d.groupby("nba_player_id", sort=False)["_y0"].idxmin()
    rook = d.loc[idx, ["nba_player_id", "Pos"]].copy()
    rook["_pos_group"] = rook["Pos"].map(_rookie_pos_code)
    return rook[["nba_player_id", "_pos_group"]]


def attach_nba_demographics_for_eda(
    df: pd.DataFrame,
    model_base: pd.DataFrame,
    *,
    copy: bool = True,
) -> pd.DataFrame:
    """
    Add ``nba_debut_age`` and rookie-season position dummies for EDA or modeling prep.

    Requires columns ``nba_player_id``, ``birthday``, ``first_season_start_year`` on ``df``.
    """
    out = df.copy() if copy else df
    birth = pd.to_datetime(out["birthday"], errors="coerce")
    out["nba_debut_age"] = out["first_season_start_year"] - birth.dt.year
    rook = _rookie_season_pos_from_model_base(model_base)
    out = out.merge(rook, on="nba_player_id", how="left")
    grp = out["_pos_group"].fillna("UNK")
    out["pos_is_SG"] = (grp == "SG").astype(float)
    out["pos_is_SF"] = (grp == "SF").astype(float)
    out["pos_is_PF"] = (grp == "PF").astype(float)
    out["pos_is_C"] = (grp == "C").astype(float)
    out["pos_is_UNK"] = (grp == "UNK").astype(float)
    return out.drop(columns=["_pos_group"], errors="ignore")


def supervised_feature_columns(_df: pd.DataFrame) -> list[str]:
    """Ordered feature columns for modeling (stable for pipelines and permutation importance)."""
    return [
        *DEMOGRAPHIC_FEATURE_COLS,
        *CBB_ADVANCED_FEATURE_COLS,
    ]


FEATURE_COLS: Final[list[str]] = list(supervised_feature_columns(pd.DataFrame()))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_supervised_frame(
    *,
    model_base_path: Path | None = None,
    summary_path: Path | None = None,
    require_non_null_bpm: bool = True,
) -> pd.DataFrame:
    """
    One row per eligible NBA player with features and target.

    Filters:
    - Deduped NBA seasons (2TM rule), then one row per ``nba_player_id``.
    - Merge career summary; keep tier D, entry_cohort, college_player_id present,
      ``success_composite_v1`` non-null.
    - If ``require_non_null_bpm``, drop rows where ``cbb_advanced_BPM`` is missing
      (Sports Reference sometimes omits BPM on a season row).
    """
    root = _repo_root()
    mb_path = model_base_path or root / "data" / "processed" / "model_base_player_season.csv"
    sm_path = summary_path or root / "data" / "processed" / "player_career_summary_v1.csv"

    mb = pd.read_csv(mb_path)
    ded = dedupe_nba_player_season(mb)
    players = ded.drop_duplicates(subset=["nba_player_id"], keep="first").copy()

    summ = pd.read_csv(sm_path)
    base = players.merge(summ, on="nba_player_id", how="left", validate="one_to_one")

    has_college = base["college_player_id"].notna() & (
        base["college_player_id"].astype(str).str.len() > 0
    )
    mask = (
        base["nba_run_tier"].eq("D")
        & base["entry_cohort"].fillna(False)
        & has_college
        & base[TARGET_COL].notna()
    )
    out = base.loc[mask].copy()

    if require_non_null_bpm:
        out = out.loc[out[BPM_COL].notna()].copy()

    out = attach_nba_demographics_for_eda(out, mb, copy=False)

    missing_cbb = [c for c in CBB_ADVANCED_FEATURE_COLS if c not in out.columns]
    if missing_cbb:
        raise KeyError(f"model_base missing columns: {missing_cbb}")

    feat = supervised_feature_columns(out)
    keep = ["nba_player_id"] + feat + [TARGET_COL]
    return out[keep].reset_index(drop=True)
