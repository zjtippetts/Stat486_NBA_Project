"""End-to-end NBA + college data pull orchestrator."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .fetch_college_profiles import fetch_college_profiles
from .fetch_nba_player_ids import NbaSeasonConfig, fetch_nba_player_ids_for_seasons, get_unique_nba_players
from .fetch_nba_player_profiles import fetch_nba_player_profiles
from .normalize_tables import write_normalized_tables


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_dirs(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


# NBA advanced table metrics (totals rows in long format leave these NaN; merge from table_id=advanced).
_NBA_ADVANCED_METRIC_COLS: tuple[str, ...] = (
    "PER",
    "TSpct",
    "3PAr",
    "FTr",
    "ORBpct",
    "DRBpct",
    "TRBpct",
    "ASTpct",
    "STLpct",
    "BLKpct",
    "TOVpct",
    "USGpct",
    "OWS",
    "DWS",
    "WS",
    "WS_48",
    "OBPM",
    "DBPM",
    "BPM",
    "VORP",
)


def _merge_nba_advanced_onto_base(base: pd.DataFrame, nba_tables_long: pd.DataFrame) -> pd.DataFrame:
    """Fill advanced-only columns on per-season totals rows from table_id=advanced."""
    if base.empty or nba_tables_long.empty or "table_id" not in nba_tables_long.columns:
        return base
    adv = nba_tables_long[nba_tables_long["table_id"] == "advanced"].copy()
    if adv.empty:
        return base
    if "Season" in adv.columns:
        adv = adv[adv["Season"].astype(str).str.match(r"^\d{4}-\d{2}$", na=False)]
    keys = ("nba_player_id", "Season")
    if not all(k in adv.columns and k in base.columns for k in keys):
        return base
    present = [c for c in _NBA_ADVANCED_METRIC_COLS if c in adv.columns]
    if not present:
        return base
    patch = adv[list(keys) + present].drop_duplicates(subset=list(keys), keep="first")
    for c in present:
        if c not in base.columns:
            base[c] = pd.NA
    merged = base.merge(patch, on=list(keys), how="left", suffixes=("", "_from_adv"))
    for c in present:
        from_c = f"{c}_from_adv"
        if from_c not in merged.columns:
            continue
        merged[c] = merged[from_c].where(merged[from_c].notna(), merged[c])
        merged = merged.drop(columns=[from_c])
    return merged


def _season_start_from_str(season_str: str) -> float:
    if not isinstance(season_str, str):
        return float("-inf")
    if len(season_str) >= 4 and season_str[:4].isdigit():
        return float(int(season_str[:4]))
    return float("-inf")


def _nba_scrape_failures_log(profile_df: pd.DataFrame) -> pd.DataFrame:
    """Rows for scrape_failures.csv from failed NBA profile fetches."""
    err = profile_df[profile_df["scrape_status"] == "error"]
    if err.empty:
        return pd.DataFrame(columns=["player_id", "player_url", "error"])
    return err[["nba_player_id", "nba_player_url", "error"]].rename(
        columns={"nba_player_id": "player_id", "nba_player_url": "player_url"}
    )


def _build_crosswalk(profile_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "nba_player_id",
        "nba_player_url",
        "college_player_id",
        "college_url",
        "birthday",
        "recruiting_year",
        "recruiting_rank",
        "scrape_status",
        "error",
    ]
    return profile_df[cols].copy()


def _build_model_base_player_season(
    nba_tables_long: pd.DataFrame,
    crosswalk_df: pd.DataFrame,
    college_tables_long: pd.DataFrame,
) -> pd.DataFrame:
    if nba_tables_long.empty:
        return pd.DataFrame()

    nba_totals = nba_tables_long[nba_tables_long["table_id"] == "totals"].copy()
    if "Season" in nba_totals.columns:
        nba_totals = nba_totals[nba_totals["Season"].astype(str).str.match(r"^\d{4}-\d{2}$", na=False)]
    # Drop BR spacer rows: season label present but no games / minutes (no usable stats or advanced join).
    if "G" in nba_totals.columns and "MP" in nba_totals.columns:
        nba_totals = nba_totals[nba_totals["G"].notna() & nba_totals["MP"].notna()]

    base = nba_totals.merge(crosswalk_df, on="nba_player_id", how="left")
    base = _merge_nba_advanced_onto_base(base, nba_tables_long)

    if college_tables_long.empty:
        return base

    college_career_frames: list[pd.DataFrame] = []
    for tid in ["totals", "per100", "advanced"]:
        frame = college_tables_long[college_tables_long["table_id"] == tid].copy()
        if frame.empty:
            continue

        if "Season" in frame.columns:
            career_rows = frame[frame["Season"].astype(str).str.lower() == "career"].copy()
            if career_rows.empty:
                frame["__season_start"] = frame["Season"].astype(str).map(_season_start_from_str)
                career_rows = (
                    frame.sort_values("__season_start")
                    .groupby("college_player_id", as_index=False)
                    .tail(1)
                    .drop(columns=["__season_start"])
                )
        else:
            career_rows = (
                frame.sort_values("college_player_id")
                .groupby("college_player_id", as_index=False)
                .tail(1)
            )

        drop_cols = {"table_id", "college_url"}
        keep_cols = [c for c in career_rows.columns if c not in drop_cols]
        career_rows = career_rows[keep_cols].copy()
        rename_map = {c: f"cbb_{tid}_{c}" for c in career_rows.columns if c != "college_player_id"}
        career_rows = career_rows.rename(columns=rename_map)
        college_career_frames.append(career_rows)

    if not college_career_frames:
        return base

    cbb_wide = college_career_frames[0]
    for extra in college_career_frames[1:]:
        cbb_wide = cbb_wide.merge(extra, on="college_player_id", how="outer")

    return base.merge(cbb_wide, on="college_player_id", how="left")


def run_data_pull(start_season: int = 2011, end_season: int = 2025, max_players: int | None = None) -> dict:
    root = _repo_root()
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    _ensure_dirs(raw_dir, processed_dir)

    config = NbaSeasonConfig(start_season=start_season, end_season=end_season)
    season_df = fetch_nba_player_ids_for_seasons(config.seasons())
    season_df = season_df.drop_duplicates(subset=["season", "nba_player_id"], keep="first").reset_index(drop=True)
    season_file = raw_dir / f"nba_season_player_ids_{start_season}_{end_season}.csv"
    season_df.to_csv(season_file, index=False)

    unique_players_df = get_unique_nba_players(season_df)
    if max_players is not None:
        unique_players_df = unique_players_df.head(max_players).copy()
    player_dicts = unique_players_df.to_dict(orient="records")

    profile_df, nba_tables_long = fetch_nba_player_profiles(player_dicts)
    profile_file = raw_dir / "nba_player_profile_fields.csv"
    nba_tables_file = raw_dir / "nba_player_tables_long.csv"
    profile_df.to_csv(profile_file, index=False)
    nba_tables_long.to_csv(nba_tables_file, index=False)

    nba_failures_df = _nba_scrape_failures_log(profile_df)
    nba_failures_df.to_csv(raw_dir / "scrape_failures.csv", index=False)

    crosswalk_df = _build_crosswalk(profile_df)
    crosswalk_file = processed_dir / "player_id_crosswalk.csv"
    crosswalk_df.to_csv(crosswalk_file, index=False)

    college_rows_df = crosswalk_df[
        crosswalk_df["college_url"].notna() & crosswalk_df["college_player_id"].notna()
    ][["college_player_id", "college_url"]].drop_duplicates()
    college_tables_long, college_failures_df = fetch_college_profiles(college_rows_df.to_dict(orient="records"))
    college_tables_file = raw_dir / "college_player_tables_long.csv"
    college_tables_long.to_csv(college_tables_file, index=False)

    scrape_failures = pd.concat(
        [
            nba_failures_df,
            college_failures_df.rename(columns={"college_player_id": "player_id", "college_url": "player_url"}),
        ],
        ignore_index=True,
        sort=False,
    )
    scrape_failures.to_csv(raw_dir / "scrape_failures.csv", index=False)

    model_base_df = _build_model_base_player_season(nba_tables_long, crosswalk_df, college_tables_long)
    model_base_file = processed_dir / "model_base_player_season.csv"
    model_base_df.to_csv(model_base_file, index=False)

    normalized_counts = write_normalized_tables(raw_dir, processed_dir, season_ids_path=season_file)

    summary: dict = {
        "seasons_requested": len(config.seasons()),
        "season_rows": int(len(season_df)),
        "unique_players": int(len(unique_players_df)),
        "profiles_ok": int((profile_df["scrape_status"] == "ok").sum()) if not profile_df.empty else 0,
        "profiles_error": int((profile_df["scrape_status"] == "error").sum()) if not profile_df.empty else 0,
        "missing_college_link": int(profile_df["college_url"].isna().sum()) if not profile_df.empty else 0,
        "nba_table_rows": int(len(nba_tables_long)),
        "college_table_rows": int(len(college_tables_long)),
        "model_rows": int(len(model_base_df)),
        "max_players_used": int(max_players) if max_players is not None else None,
    }
    for key, n in normalized_counts.items():
        summary[f"norm_{key}"] = n
    pd.DataFrame([summary]).to_csv(raw_dir / "scrape_summary.csv", index=False)
    return summary


if __name__ == "__main__":
    result = run_data_pull(start_season=2011, end_season=2025)
    print("Data pull complete.")
    for key, value in result.items():
        print(f"{key}: {value}")
