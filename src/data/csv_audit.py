"""Scan data/raw and data/processed CSVs for empty rows, full-row duplicates, and key duplicates."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _empty_row_count(df: pd.DataFrame) -> int:
    """Rows where every cell is NA or blank string."""
    if df.empty:
        return 0
    x = df.copy()
    for c in x.columns:
        if x[c].dtype == object or str(x[c].dtype) == "string":
            x[c] = x[c].replace(r"^\s*$", np.nan, regex=True)
    return int(x.isna().all(axis=1).sum())


def _full_row_dup_count(df: pd.DataFrame) -> int:
    return int(df.duplicated(keep=False).sum())


def _key_dup_count(df: pd.DataFrame, key_cols: list[str]) -> tuple[int, list[str]]:
    missing = [c for c in key_cols if c not in df.columns]
    if missing:
        return 0, missing
    sub = df[key_cols].copy()
    for c in sub.columns:
        sub[c] = sub[c].fillna("__NA__")
    dup_rows = sub.duplicated(keep=False)
    return int(dup_rows.sum()), []


def _rules_for_name(name: str) -> list[str] | None:
    """Return key columns that should be unique. None = skip key check."""
    if name == "scrape_summary.csv":
        return None
    if name in ("player_id_crosswalk.csv", "players.csv", "nba_college_map.csv"):
        return ["nba_player_id"]
    if name == "nba_season_appearances.csv":
        return ["season", "nba_player_id"]
    return []


def audit_csv(path: Path) -> tuple[list[str], list[str]]:
    """
    Return (issues, notes).

    issues: problems to fix; notes: expected quirks / FYI.
    """
    name = path.name
    issues: list[str] = []
    notes: list[str] = []
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as exc:  # noqa: BLE001
        return ([f"{path.name}: cannot read ({exc})"], [])

    if df.empty:
        if name == "scrape_failures.csv":
            return ([], [])
        return ([f"{path.name}: 0 data rows"], [])

    n = len(df)
    empty = _empty_row_count(df)
    if empty:
        issues.append(f"{path.name}: {empty} all-empty row(s) (of {n})")

    key_rule = _rules_for_name(name)
    if key_rule is not None and key_rule:
        kd, missing = _key_dup_count(df, key_rule)
        if missing:
            issues.append(f"{path.name}: key rule {key_rule} - missing columns {missing}")
        elif kd:
            issues.append(
                f"{path.name}: {kd} row(s) duplicate on key {key_rule} (non-unique keys)",
            )

    # Raw league list: duplicates expected until run_data_pull re-saves deduped raw
    if name.startswith("nba_season_player_ids_"):
        kd_raw, _ = _key_dup_count(df, ["season", "nba_player_id"])
        if kd_raw:
            notes.append(
                f"{path.name}: {kd_raw} row(s) share a (season, nba_player_id) - normal for raw "
                f"BR totals (multi-team stints). Processed nba_season_appearances.csv is deduped. "
                f"Re-run run_data_pull to dedupe this raw file.",
            )

    has_season = "Season" in df.columns and df["Season"].notna().any()
    has_team = "Team" in df.columns

    # Full-row duplicates only when Season exists (otherwise many tables look falsely duplicated)
    dup_subset = df
    if name == "nba_player_tables_long.csv" and "Season" in df.columns:
        dup_subset = df[df["Season"].notna()].copy()
    if has_season and len(dup_subset):
        full_d = _full_row_dup_count(dup_subset)
        if full_d:
            scope = f"({len(dup_subset)} rows with Season)" if name == "nba_player_tables_long.csv" else f"({n} rows)"
            issues.append(
                f"{path.name}: {full_d} row(s) in exact duplicate row groups {scope}",
            )

    # Normalized per-player stat tables: one row per (player, season, team stint)
    stat_tables = {
        "nba_totals.csv",
        "nba_per100.csv",
        "nba_advanced.csv",
        "nba_adj_shooting.csv",
        "nba_shooting.csv",
        "cbb_totals.csv",
        "cbb_per100.csv",
        "cbb_advanced.csv",
    }
    if name in stat_tables and has_season and has_team:
        if name.startswith("nba"):
            kd2, _ = _key_dup_count(df, ["nba_player_id", "Season", "Team"])
            if kd2:
                issues.append(
                    f"{path.name}: {kd2} row(s) duplicate on [nba_player_id, Season, Team]",
                )
        elif name.startswith("cbb"):
            kd3, _ = _key_dup_count(df, ["college_player_id", "Season", "Team"])
            if kd3:
                issues.append(
                    f"{path.name}: {kd3} row(s) duplicate on [college_player_id, Season, Team]",
                )

    if name in ("nba_adj_shooting.csv", "nba_shooting.csv") and not has_season:
        notes.append(
            f"{path.name}: no Season values in file (BR shooting blocks often omit season columns); "
            f"full-row duplicate checks skipped - use raw nba_player_tables_long + table_id if you need row identity.",
        )

    if name == "nba_player_tables_long.csv":
        if not {"nba_player_id", "table_id", "Season", "Team"}.issubset(df.columns):
            issues.append(f"{path.name}: expected columns nba_player_id, table_id, Season, Team")
        else:
            sub = df[df["Season"].notna()].copy()
            if len(sub):
                kd4, _ = _key_dup_count(sub, ["nba_player_id", "table_id", "Season", "Team"])
                if kd4:
                    issues.append(
                        f"{path.name}: {kd4} row(s) duplicate on "
                        f"[nba_player_id, table_id, Season, Team] (among rows with Season)",
                    )
            lost = df["Season"].isna().sum()
            if lost:
                by_tid = df[df["Season"].isna()].groupby("table_id").size()
                top = by_tid.sort_values(ascending=False).head(3)
                notes.append(
                    f"{path.name}: {int(lost)} row(s) with missing Season (by table_id: "
                    f"{', '.join(f'{k}={v}' for k, v in top.items())} ...); not counted in key-dup check.",
                )

    if name == "college_player_tables_long.csv" and {
        "college_player_id",
        "table_id",
        "Season",
        "Team",
    }.issubset(df.columns):
        sub = df[df["Season"].notna()].copy()
        if len(sub):
            kd5, _ = _key_dup_count(sub, ["college_player_id", "table_id", "Season", "Team"])
            if kd5:
                issues.append(
                    f"{path.name}: {kd5} row(s) duplicate on "
                    f"[college_player_id, table_id, Season, Team] (among rows with Season)",
                )

    if name == "model_base_player_season.csv" and {"nba_player_id", "Season", "Team"}.issubset(df.columns):
        kd6, _ = _key_dup_count(df, ["nba_player_id", "Season", "Team"])
        if kd6:
            issues.append(
                f"{path.name}: {kd6} row(s) duplicate on [nba_player_id, Season, Team]",
            )

    return issues, notes


def run_audit(raw_dir: Path | None = None, processed_dir: Path | None = None) -> int:
    root = _repo_root()
    raw_dir = Path(raw_dir) if raw_dir else root / "data" / "raw"
    processed_dir = Path(processed_dir) if processed_dir else root / "data" / "processed"

    paths = sorted(raw_dir.glob("*.csv")) + sorted(processed_dir.glob("*.csv"))
    all_issues: list[str] = []
    all_notes: list[str] = []
    for p in paths:
        iss, nts = audit_csv(p)
        all_issues.extend(iss)
        all_notes.extend(nts)

    print(f"Audited {len(paths)} CSV files under data/raw and data/processed.\n")
    if all_notes:
        print("Notes (expected / context):\n")
        for line in all_notes:
            print(f"  - {line}")
        print()
    if not all_issues:
        print("No blocking issues (empty rows, bad key uniqueness, or exact duplicate rows where Season exists).")
        return 0

    print("Issues:\n")
    for line in all_issues:
        print(f"  - {line}")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit project CSVs for duplicates and empty rows.")
    parser.add_argument("--raw", type=Path, default=None)
    parser.add_argument("--processed", type=Path, default=None)
    args = parser.parse_args()
    code = run_audit(raw_dir=args.raw, processed_dir=args.processed)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
