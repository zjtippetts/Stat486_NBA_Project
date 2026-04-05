"""
Career outcome construction aligned with progress/target_variable_spec.md (v1).

- Dedupe multi-team seasons (keep 2TM/3TM/4TM row when present).
- Qualifying season: G >= 10 and MP >= 100.
- Entry cohort: first season start year in [2011, 2022] (2011-12 … 2022-23).
- Tiers A–D; composite = 0.70*z(fantasy mean) + 0.30*z(log1p(games/opportunity)) for tier D + cohort.
  Opportunity = 82 * seasons from NBA debut through latest season in ``model_base``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

ENTRY_YEAR_MIN: Final = 2011
ENTRY_YEAR_MAX: Final = 2022
MIN_G_QUAL: Final = 10
MIN_MP_QUAL: Final = 100
# Two-part composite only (no VORP/DWS) — easier to explain for STAT 486.
# Emphasize per-game impact; longevity still nerf/bumps but does not dominate (e.g. stars with missed games).
W_FANTASY: Final = 0.70
W_LONGEVITY: Final = 0.30
# Nominal regular-season games per year for opportunity denominator (lockouts not adjusted).
REGULAR_SEASON_GAMES_PER_YEAR: Final = 82


def season_start_year(season: str | float | int) -> int:
    """Parse BR season label '2011-12' -> 2011."""
    s = str(season).strip()
    if len(s) >= 4 and s[:4].isdigit():
        return int(s[:4])
    return -1


def dedupe_nba_player_season(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per (nba_player_id, Season): prefer combined nTM row when present.
    See target_variable_spec.md section 2.1.
    """
    if df.empty:
        return df
    out = df.copy()
    team = out["Team"].astype(str)
    out["_is_ntm"] = team.str.match(r"^\d+TM$", na=False)

    def _pick(g: pd.DataFrame) -> pd.DataFrame:
        if g["_is_ntm"].any():
            return g[g["_is_ntm"]].head(1)
        return g.head(1)

    chunks: list[pd.DataFrame] = []
    for _, g in out.groupby(["nba_player_id", "Season"], sort=False):
        chunks.append(_pick(g))
    picked = pd.concat(chunks, ignore_index=True)
    return picked.drop(columns=["_is_ntm"])


def fantasy_points_season(df: pd.DataFrame) -> pd.DataFrame:
    """FP and FP_per_game (BR: FG = field goals made)."""
    out = df.copy()
    out["FP"] = (
        out["PTS"]
        + out["3P"]
        - out["FGA"]
        + 2.0 * out["FG"]
        - out["FTA"]
        + out["FT"]
        + out["TRB"]
        + 2.0 * out["AST"]
        + 4.0 * out["STL"]
        + 4.0 * out["BLK"]
        - 2.0 * out["TOV"]
    )
    out["FP_per_game"] = out["FP"] / out["G"].replace(0, np.nan)
    return out


def _tier_label(n_qual: int, career_games: float) -> str:
    cg = int(career_games) if pd.notna(career_games) else 0
    if cg <= 0:
        return "A"
    if n_qual == 0:
        return "B"
    if n_qual == 1:
        return "C"
    return "D"


def build_player_career_summary(
    model_base: pd.DataFrame,
    *,
    entry_year_min: int = ENTRY_YEAR_MIN,
    entry_year_max: int = ENTRY_YEAR_MAX,
) -> pd.DataFrame:
    """
    Player-level summary: tiers, cohort, components, composite (tier D + cohort only).

    Returns one row per nba_player_id appearing in model_base (after dedupe).
    """
    d = dedupe_nba_player_season(model_base)
    d = fantasy_points_season(d)
    d["_season_y0"] = d["Season"].map(season_start_year)

    def _agg(g: pd.DataFrame) -> pd.Series:
        career_games = float(g["G"].sum())
        q = (g["G"] >= MIN_G_QUAL) & (g["MP"] >= MIN_MP_QUAL)
        n_qual = int(q.sum())
        min_y = int(g["_season_y0"].min())
        first_season = g.loc[g["_season_y0"] == min_y, "Season"].iloc[0]
        if n_qual == 0:
            mean_fp_q = np.nan
        else:
            mean_fp_q = float(g.loc[q, "FP_per_game"].mean())

        return pd.Series(
            {
                "first_season_start_year": min_y,
                "first_season": first_season,
                "career_games": career_games,
                "n_qualifying_seasons": n_qual,
                "mean_fp_per_game_qual": mean_fp_q,
            }
        )

    gb = d.groupby("nba_player_id", sort=False)
    try:
        summ = gb.apply(_agg, include_groups=False).reset_index()
    except TypeError:
        summ = gb.apply(_agg).reset_index()

    summ["entry_cohort"] = summ["first_season_start_year"].between(entry_year_min, entry_year_max)

    summ["nba_run_tier"] = [
        _tier_label(int(r["n_qualifying_seasons"]), r["career_games"])
        for _, r in summ.iterrows()
    ]

    sy = d["_season_y0"]
    valid_end = sy[sy >= 1990]
    window_end_year = int(valid_end.max()) if len(valid_end) else int(np.nanmax(sy.to_numpy(dtype=float)))
    summ["longevity_window_end_year"] = window_end_year
    deb = summ["first_season_start_year"]
    ok_debut = deb.between(1990, window_end_year)
    summ["longevity_eligible_seasons"] = np.where(
        ok_debut,
        np.maximum(1, window_end_year - deb + 1),
        np.nan,
    )
    summ["longevity_nominal_max_games"] = (
        summ["longevity_eligible_seasons"] * REGULAR_SEASON_GAMES_PER_YEAR
    )
    summ["longevity_games_vs_opportunity"] = summ["career_games"] / summ[
        "longevity_nominal_max_games"
    ]

    eligible_mask = (summ["nba_run_tier"] == "D") & summ["entry_cohort"]
    sub = summ.loc[eligible_mask].copy()

    def _z(x: pd.Series) -> pd.Series:
        mu = x.mean()
        sd = x.std(ddof=0)
        if sd == 0 or np.isnan(sd):
            return pd.Series(np.nan, index=x.index)
        return (x - mu) / sd

    summ["z_fantasy"] = np.nan
    summ["z_longevity"] = np.nan
    summ["success_composite_v1"] = np.nan

    if not sub.empty:
        zf = _z(sub["mean_fp_per_game_qual"])
        # z-score log1p(share of nominal regular-season games vs opportunity window)
        zl = _z(np.log1p(sub["longevity_games_vs_opportunity"]))
        idx = sub.index
        summ.loc[idx, "z_fantasy"] = zf.values
        summ.loc[idx, "z_longevity"] = zl.values
        summ.loc[idx, "success_composite_v1"] = (
            W_FANTASY * summ.loc[idx, "z_fantasy"]
            + W_LONGEVITY * summ.loc[idx, "z_longevity"]
        )

    return summ


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> None:
    root = _repo_root()
    path = root / "data" / "processed" / "model_base_player_season.csv"
    df = pd.read_csv(path)
    deduped = dedupe_nba_player_season(df)
    assert deduped.groupby(["nba_player_id", "Season"]).size().max() == 1, "dedupe failed"

    summ = build_player_career_summary(df)
    print("Players:", len(summ))
    print("Tier counts:\n", summ["nba_run_tier"].value_counts().sort_index())
    print("Entry cohort:", summ["entry_cohort"].sum())
    print(
        "Tier D + cohort (composite):",
        summ["success_composite_v1"].notna().sum(),
    )
    out_csv = root / "data" / "processed" / "player_career_summary_v1.csv"
    summ.to_csv(out_csv, index=False)
    print("Wrote", out_csv)


if __name__ == "__main__":
    main()
