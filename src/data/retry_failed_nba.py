"""Re-fetch NBA player pages listed in scrape_failures.csv and merge into existing CSVs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .fetch_college_profiles import fetch_college_profiles
from .fetch_nba_player_profiles import fetch_nba_player_profiles
from .normalize_tables import write_normalized_tables
from .run_data_pull import _build_crosswalk, _build_model_base_player_season
from .validate_data import rebuild_scrape_failures_from_profiles


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def retry_failed_nba_profiles(*, max_workers: int = 3) -> None:
    root = _repo_root()
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"

    fail_path = raw_dir / "scrape_failures.csv"
    if not fail_path.exists():
        raise FileNotFoundError(fail_path)

    fails = pd.read_csv(fail_path)
    br = fails[fails["player_url"].astype(str).str.contains("basketball-reference.com", na=False)]
    if br.empty:
        print("No Basketball-Reference rows in scrape_failures.csv; nothing to retry.")
        return

    players = [
        {"nba_player_id": row.player_id, "nba_player_url": row.player_url}
        for row in br.itertuples(index=False)
    ]
    print(f"Retrying {len(players)} NBA profiles (max_workers={max_workers})...")
    new_prof, new_tables = fetch_nba_player_profiles(players, max_workers=max_workers)

    prof_path = raw_dir / "nba_player_profile_fields.csv"
    existing_prof = pd.read_csv(prof_path)
    ids = set(new_prof["nba_player_id"])
    merged_prof = pd.concat(
        [existing_prof[~existing_prof["nba_player_id"].isin(ids)], new_prof],
        ignore_index=True,
    ).sort_values("nba_player_id", kind="mergesort").reset_index(drop=True)
    merged_prof.to_csv(prof_path, index=False)

    tables_path = raw_dir / "nba_player_tables_long.csv"
    existing_tables = pd.read_csv(tables_path)
    merged_tables = pd.concat(
        [existing_tables[~existing_tables["nba_player_id"].isin(ids)], new_tables],
        ignore_index=True,
    )
    merged_tables.to_csv(tables_path, index=False)

    crosswalk = _build_crosswalk(merged_prof)
    crosswalk.to_csv(processed_dir / "player_id_crosswalk.csv", index=False)

    cbb_path = raw_dir / "college_player_tables_long.csv"
    existing_cbb = pd.read_csv(cbb_path) if cbb_path.exists() else pd.DataFrame()

    ok_with_college = new_prof[
        (new_prof["scrape_status"] == "ok") & new_prof["college_url"].notna() & new_prof["college_player_id"].notna()
    ]
    if not ok_with_college.empty:
        jobs = ok_with_college[["college_player_id", "college_url"]].drop_duplicates()
        cid_set = set(jobs["college_player_id"].astype(str))
        trimmed = (
            existing_cbb[~existing_cbb["college_player_id"].astype(str).isin(cid_set)]
            if not existing_cbb.empty
            else existing_cbb
        )
        cbb_new, _ = fetch_college_profiles(jobs.to_dict(orient="records"), max_workers=max_workers)
        merged_cbb = pd.concat([trimmed, cbb_new], ignore_index=True) if not cbb_new.empty else trimmed
        merged_cbb.to_csv(cbb_path, index=False)
    else:
        merged_cbb = existing_cbb

    model_base = _build_model_base_player_season(merged_tables, crosswalk, merged_cbb)
    model_base.to_csv(processed_dir / "model_base_player_season.csv", index=False)

    season_files = sorted(raw_dir.glob("nba_season_player_ids_*.csv"))
    season_path = season_files[-1] if season_files else None
    write_normalized_tables(raw_dir, processed_dir, season_ids_path=season_path)

    rebuild_scrape_failures_from_profiles(raw_dir)

    n_ok = int((new_prof["scrape_status"] == "ok").sum())
    n_err = int((new_prof["scrape_status"] == "error").sum())
    print(f"Batch result: ok={n_ok}, still error={n_err}. Merged into data/raw and data/processed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retry NBA profiles listed in scrape_failures.csv")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        metavar="N",
        help="Concurrent player fetches (lower = fewer 429s; default 3)",
    )
    args = parser.parse_args()
    retry_failed_nba_profiles(max_workers=max(1, args.max_workers))


if __name__ == "__main__":
    main()
