"""Print row counts, join-key sanity, and obvious gaps in raw/processed CSVs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from .normalize_tables import CBB_TABLE_IDS, NBA_TABLE_IDS


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8", errors="replace") as f:
        return max(0, sum(1 for _ in f) - 1)


def refresh_scrape_summary_from_disk(
    raw_dir: Path | None = None,
    processed_dir: Path | None = None,
) -> dict:
    """Rebuild scrape_summary.csv from current raw/processed files (no scraping)."""
    root = _repo_root()
    raw_dir = Path(raw_dir) if raw_dir else root / "data" / "raw"
    processed_dir = Path(processed_dir) if processed_dir else root / "data" / "processed"

    prof = pd.read_csv(raw_dir / "nba_player_profile_fields.csv")
    season_files = sorted(raw_dir.glob("nba_season_player_ids_*.csv"))
    if not season_files:
        raise FileNotFoundError("No nba_season_player_ids_*.csv in raw/")
    season_path = season_files[-1]
    season_df = pd.read_csv(season_path)

    m = re.search(r"nba_season_player_ids_(\d+)_(\d+)\.csv", season_path.name)
    if m:
        seasons_requested = int(m.group(2)) - int(m.group(1)) + 1
    else:
        seasons_requested = int(season_df["season"].nunique()) if "season" in season_df.columns else 0

    nba_long_n = _csv_row_count(raw_dir / "nba_player_tables_long.csv")
    cbb_long_n = _csv_row_count(raw_dir / "college_player_tables_long.csv")
    model_n = _csv_row_count(processed_dir / "model_base_player_season.csv")

    summary: dict = {
        "seasons_requested": seasons_requested,
        "season_rows": int(len(season_df)),
        "unique_players": int(len(prof)),
        "profiles_ok": int((prof["scrape_status"] == "ok").sum()) if not prof.empty else 0,
        "profiles_error": int((prof["scrape_status"] == "error").sum()) if not prof.empty else 0,
        "missing_college_link": int(prof["college_url"].isna().sum()) if "college_url" in prof.columns else 0,
        "nba_table_rows": nba_long_n,
        "college_table_rows": cbb_long_n,
        "model_rows": model_n,
        "max_players_used": None,
    }

    summary["norm_players"] = _csv_row_count(processed_dir / "players.csv")
    summary["norm_nba_college_map"] = _csv_row_count(processed_dir / "nba_college_map.csv")
    summary["norm_nba_season_appearances"] = _csv_row_count(processed_dir / "nba_season_appearances.csv")
    for tid in NBA_TABLE_IDS:
        summary[f"norm_nba_{tid}"] = _csv_row_count(processed_dir / f"nba_{tid}.csv")
    for tid in CBB_TABLE_IDS:
        summary[f"norm_cbb_{tid}"] = _csv_row_count(processed_dir / f"cbb_{tid}.csv")

    pd.DataFrame([summary]).to_csv(raw_dir / "scrape_summary.csv", index=False)
    return summary


def readiness_checks(
    raw_dir: Path | None = None,
    processed_dir: Path | None = None,
) -> tuple[list[str], list[str]]:
    """
    Return (blocking_issues, warnings).

    Blocking: bad profile status, id mismatches, stale failure log.
    Warnings: college long file missing many crosswalk slugs (needs backfill).
    """
    root = _repo_root()
    raw_dir = Path(raw_dir) if raw_dir else root / "data" / "raw"
    processed_dir = Path(processed_dir) if processed_dir else root / "data" / "processed"
    blocking: list[str] = []
    warnings: list[str] = []

    prof_path = raw_dir / "nba_player_profile_fields.csv"
    if not prof_path.exists():
        return (["Missing nba_player_profile_fields.csv"], [])
    prof = pd.read_csv(prof_path)
    n_bad = int((prof["scrape_status"] != "ok").sum()) if "scrape_status" in prof.columns else 0
    if n_bad:
        blocking.append(f"{n_bad} profile row(s) with scrape_status != ok")

    season_files = sorted(raw_dir.glob("nba_season_player_ids_*.csv"))
    if season_files:
        season_df = pd.read_csv(season_files[-1])
        ids_season = set(season_df["nba_player_id"].astype(str))
        ids_prof = set(prof["nba_player_id"].astype(str))
        if ids_season != ids_prof:
            missing = len(ids_season - ids_prof)
            extra = len(ids_prof - ids_season)
            if missing:
                blocking.append(f"{missing} player id(s) in season list but not in profiles")
            if extra:
                blocking.append(f"{extra} player id(s) in profiles but not in season list")

    cw_path = processed_dir / "player_id_crosswalk.csv"
    if cw_path.exists():
        cw = pd.read_csv(cw_path)
        if len(cw) != len(prof):
            blocking.append(
                f"crosswalk rows ({len(cw)}) != profile rows ({len(prof)})",
            )

    cbb_path = raw_dir / "college_player_tables_long.csv"
    cw = pd.read_csv(cw_path) if cw_path.exists() else pd.DataFrame()
    if cbb_path.exists() and cbb_path.stat().st_size > 10 and not cw.empty:
        cbb = pd.read_csv(cbb_path, usecols=["college_player_id"])
        cbb_ids = set(cbb["college_player_id"].astype(str))
        if "college_player_id" in cw.columns:
            need = cw[cw["college_player_id"].notna() & cw["college_url"].notna()]
            need_u = set(need["college_player_id"].dropna().astype(str))
            missing_cbb = need_u - cbb_ids
            if missing_cbb:
                n_m = len(missing_cbb)
                warnings.append(
                    f"{n_m} distinct college_player_id(s) in crosswalk have no rows in "
                    f"college_player_tables_long (need college backfill for full CBB features). "
                    f"Run: python -m src.data.backfill_college",
                )

    fail_path = raw_dir / "scrape_failures.csv"
    if fail_path.exists():
        fails = pd.read_csv(fail_path)
        if len(fails) and n_bad == 0:
            blocking.append("scrape_failures.csv has rows but all profiles are ok (stale failures log?)")

    return blocking, warnings


def rebuild_scrape_failures_from_profiles(raw_dir: Path | None = None) -> int:
    """
    Rewrite data/raw/scrape_failures.csv using NBA errors in nba_player_profile_fields.csv.

    Use if scrape_failures.csv is empty but profiles show scrape_status == error (e.g. run
    stopped before the final concat). College scrape failures are not reconstructed here.
    """
    raw_dir = Path(raw_dir) if raw_dir else _repo_root() / "data" / "raw"
    prof_path = raw_dir / "nba_player_profile_fields.csv"
    if not prof_path.exists():
        raise FileNotFoundError(prof_path)
    df = pd.read_csv(prof_path)
    err = df[df["scrape_status"] == "error"]
    if err.empty:
        out = pd.DataFrame(columns=["player_id", "player_url", "error"])
    else:
        out = err[["nba_player_id", "nba_player_url", "error"]].rename(
            columns={"nba_player_id": "player_id", "nba_player_url": "player_url"}
        )
    out.to_csv(raw_dir / "scrape_failures.csv", index=False)
    return int(len(out))


def validate_data(raw_dir: Path | None = None, processed_dir: Path | None = None) -> None:
    root = _repo_root()
    raw_dir = Path(raw_dir) if raw_dir else root / "data" / "raw"
    processed_dir = Path(processed_dir) if processed_dir else root / "data" / "processed"

    print("=== Paths ===")
    print(f"raw:       {raw_dir}")
    print(f"processed: {processed_dir}")
    print()

    summary_path = raw_dir / "scrape_summary.csv"
    if summary_path.exists():
        print("=== scrape_summary.csv (latest run) ===")
        print(pd.read_csv(summary_path).T.to_string(header=False))
        print()

    fail_path = raw_dir / "scrape_failures.csv"
    if fail_path.exists():
        fails = pd.read_csv(fail_path)
        print(f"=== scrape_failures.csv ({len(fails)} rows) ===")
        if len(fails):
            print(fails.to_string(max_rows=15))
        print()

    prof_path = raw_dir / "nba_player_profile_fields.csv"
    if prof_path.exists():
        p = pd.read_csv(prof_path)
        print("=== nba_player_profile_fields.csv ===")
        print(f"rows: {len(p)}")
        if "scrape_status" in p.columns:
            print("scrape_status:\n", p["scrape_status"].value_counts(dropna=False).to_string())
        if "college_url" in p.columns:
            n = p["college_url"].isna().sum()
            print(f"missing college_url: {n} ({100 * n / len(p):.1f}%)")
        print()

    season_glob = sorted(raw_dir.glob("nba_season_player_ids_*.csv"))
    if season_glob:
        s = pd.read_csv(season_glob[-1])
        print(f"=== {season_glob[-1].name} ===")
        print(f"rows (season list incl. multi-team): {len(s)}")
        print(f"unique nba_player_id: {s['nba_player_id'].nunique()}")
        if "season" in s.columns:
            print(f"season range: {s['season'].min()} – {s['season'].max()}")
        print()

    cw_path = processed_dir / "player_id_crosswalk.csv"
    if cw_path.exists():
        cw = pd.read_csv(cw_path)
        print("=== player_id_crosswalk.csv ===")
        print(f"rows: {len(cw)}")
        if "college_player_id" in cw.columns:
            m = cw["college_player_id"].notna().sum()
            print(f"with college_player_id: {m} ({100 * m / len(cw):.1f}%)")
        print()

    nba_long = raw_dir / "nba_player_tables_long.csv"
    if nba_long.exists():
        # Only read table_id column for speed on large files
        tid = pd.read_csv(nba_long, usecols=["table_id"])
        print("=== nba_player_tables_long.csv (by table_id) ===")
        print(tid["table_id"].value_counts(dropna=False).to_string())
        print()

    cbb_long = raw_dir / "college_player_tables_long.csv"
    if cbb_long.exists():
        tid = pd.read_csv(cbb_long, usecols=["table_id"])
        print("=== college_player_tables_long.csv (by table_id) ===")
        print(tid["table_id"].value_counts(dropna=False).to_string())
        print()

    nba_tot = processed_dir / "nba_totals.csv"
    if nba_tot.exists():
        t = pd.read_csv(nba_tot, usecols=["nba_player_id", "Season"])
        print("=== nba_totals.csv (grain spot-check) ===")
        print(f"rows: {len(t)}")
        season_like = t["Season"].astype(str).str.match(r"^\d{4}-\d{2}$", na=False)
        print(f"rows with Season like YYYY-YY: {season_like.sum()}")
        print(f"unique (nba_player_id, Season) rows: {t.drop_duplicates().shape[0]}")
        print()

    print("Tip: open notebooks/ or run pandas in Jupyter for deeper checks (filters, plots).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate raw/processed CSVs after a data pull.")
    parser.add_argument(
        "--repair-failures",
        action="store_true",
        help="Rebuild scrape_failures.csv from nba_player_profile_fields.csv (NBA errors only).",
    )
    parser.add_argument(
        "--refresh-summary",
        action="store_true",
        help="Rewrite scrape_summary.csv from current CSVs (fixes stale counts after retry/normalize).",
    )
    parser.add_argument(
        "--readiness",
        action="store_true",
        help="Run integrity checks only (season list vs profiles, crosswalk vs CBB, etc.).",
    )
    args = parser.parse_args()
    if args.repair_failures:
        n = rebuild_scrape_failures_from_profiles()
        print(f"Wrote {n} rows to data/raw/scrape_failures.csv")
    if args.refresh_summary:
        refresh_scrape_summary_from_disk()
        print("Updated data/raw/scrape_summary.csv from current files.")
    if args.readiness:
        blocking, warns = readiness_checks()
        if blocking:
            print("=== Readiness: blocking issues ===")
            for p in blocking:
                print(f"  - {p}")
        if warns:
            print("=== Readiness: warnings ===")
            for p in warns:
                print(f"  - {p}")
        if not blocking and not warns:
            print("=== Readiness: OK ===")
            print("  Profiles, season-list ids, crosswalk, and college long coverage look consistent.")
        elif not blocking:
            print("=== Readiness: OK for NBA/core joins (see warnings above) ===")
        print()

    validate_data()


if __name__ == "__main__":
    main()
