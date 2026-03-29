"""Fetch college stat tables for crosswalk players missing from college_player_tables_long.csv."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

from .fetch_college_profiles import fetch_college_profiles
from .run_data_pull import _build_model_base_player_season
from .normalize_tables import write_normalized_tables


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def backfill_missing_college(
    *,
    max_workers: int = 4,
    quiet: bool = False,
    progress_every: int = 25,
) -> dict:
    root = _repo_root()
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"

    cw = pd.read_csv(processed_dir / "player_id_crosswalk.csv")
    need = cw[cw["college_player_id"].notna() & cw["college_url"].notna()][
        ["college_player_id", "college_url"]
    ].drop_duplicates()

    cbb_path = raw_dir / "college_player_tables_long.csv"
    existing = pd.read_csv(cbb_path) if cbb_path.exists() else pd.DataFrame()
    have: set[str] = set()
    if not existing.empty and "college_player_id" in existing.columns:
        have = set(existing["college_player_id"].astype(str))

    missing = need[~need["college_player_id"].astype(str).isin(have)]
    n_missing = int(len(missing))
    if n_missing == 0:
        print("No missing college slugs; college_player_tables_long.csv already covers crosswalk.")
        return {"fetched_slugs": 0, "rows_added": 0, "failures": 0}

    if not quiet:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(message)s",
            datefmt="%H:%M:%S",
            force=True,
        )
    print(f"Fetching {n_missing} college player pages (max_workers={max_workers})...")
    pe = 0 if quiet else max(1, progress_every)
    new_tables, failures_df = fetch_college_profiles(
        missing.to_dict(orient="records"),
        max_workers=max_workers,
        progress_every=pe,
    )
    rows_added = int(len(new_tables))
    n_fail = int(len(failures_df)) if not failures_df.empty else 0
    if n_fail and not quiet:
        logger.info("Finished with %s college page error(s) (re-run backfill to retry).", n_fail)
    if new_tables.empty:
        print("College fetch returned no rows.")
        return {"fetched_slugs": n_missing, "rows_added": 0, "failures": n_fail}

    merged = pd.concat([existing, new_tables], ignore_index=True) if not existing.empty else new_tables
    merged.to_csv(cbb_path, index=False)

    prof = pd.read_csv(raw_dir / "nba_player_profile_fields.csv")
    nba_long = pd.read_csv(raw_dir / "nba_player_tables_long.csv")
    model = _build_model_base_player_season(nba_long, cw, merged)
    model.to_csv(processed_dir / "model_base_player_season.csv", index=False)

    season_files = sorted(raw_dir.glob("nba_season_player_ids_*.csv"))
    season_path = season_files[-1] if season_files else None
    write_normalized_tables(raw_dir, processed_dir, season_ids_path=season_path)

    print(f"Added {rows_added} college table rows; updated model_base and normalized tables.")
    return {"fetched_slugs": n_missing, "rows_added": rows_added, "failures": n_fail}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill college stats for crosswalk slugs missing from raw CBB long CSV")
    parser.add_argument("--max-workers", type=int, default=4, metavar="N")
    parser.add_argument(
        "--progress-every",
        type=int,
        default=25,
        metavar="N",
        help="Log progress every N completed pages (default 25). Set 0 to log only each page.",
    )
    parser.add_argument("--quiet", action="store_true", help="No progress logs (only final print lines).")
    args = parser.parse_args()
    pe = args.progress_every
    if pe == 0:
        pe = 1
    backfill_missing_college(
        max_workers=max(1, args.max_workers),
        quiet=args.quiet,
        progress_every=pe if not args.quiet else 0,
    )


if __name__ == "__main__":
    main()
