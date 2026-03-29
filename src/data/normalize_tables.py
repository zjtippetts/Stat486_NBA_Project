"""Split long-format scraper outputs into normalized, table-per-stat-type CSVs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

NBA_TABLE_IDS = ("totals", "per100", "advanced", "adj_shooting", "play_by_play", "shooting")
CBB_TABLE_IDS = ("totals", "per100", "advanced")


def _drop_all_null_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.dropna(axis=1, how="all")


def _dedupe_season_appearances(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (season, nba_player_id); league totals pages repeat players per team stint."""
    if df.empty or not {"season", "nba_player_id"}.issubset(df.columns):
        return df
    return df.drop_duplicates(subset=["season", "nba_player_id"], keep="first").reset_index(drop=True)


def _drop_br_spacer_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove blank separator rows Sports Reference inserts in stat tables (empty Season)."""
    if df.empty or "Season" not in df.columns:
        return df
    s = df["Season"]
    valid = s.notna() & ~s.astype(str).str.strip().isin(("", "nan"))
    return df[valid].reset_index(drop=True)


def _write_csv(df: pd.DataFrame, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return int(len(df))


def _split_by_table_id(
    long_df: pd.DataFrame,
    *,
    id_cols: tuple[str, ...],
    table_col: str = "table_id",
) -> dict[str, pd.DataFrame]:
    if long_df.empty or table_col not in long_df.columns:
        return {}
    out: dict[str, pd.DataFrame] = {}
    for tid in long_df[table_col].dropna().unique():
        tid_str = str(tid)
        part = long_df[long_df[table_col] == tid].drop(columns=[table_col])
        part = _drop_all_null_columns(part)
        # Stable column order: ids first, then rest alphabetically for readability
        rest = [c for c in part.columns if c not in id_cols]
        rest.sort()
        ordered = [c for c in id_cols if c in part.columns] + rest
        part = part[ordered]
        out[tid_str] = part
    return out


def _find_season_ids_csv(raw_dir: Path) -> Path | None:
    matches = sorted(raw_dir.glob("nba_season_player_ids_*.csv"))
    return matches[-1] if matches else None


def write_normalized_tables(
    raw_dir: Path,
    processed_dir: Path,
    *,
    season_ids_path: Path | None = None,
) -> dict[str, int]:
    """
    Build reference tables and one CSV per NBA/CBB stat table from raw long files.

    Reads:
      - nba_player_profile_fields.csv
      - player_id_crosswalk.csv (must exist after a pull)
      - nba_player_tables_long.csv
      - college_player_tables_long.csv
      - nba_season_player_ids_*.csv (latest match if season_ids_path omitted)
    Writes under processed_dir (flat layout).
    """
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}

    profile_path = raw_dir / "nba_player_profile_fields.csv"
    if profile_path.exists():
        players = pd.read_csv(profile_path)
        counts["players"] = _write_csv(players, processed_dir / "players.csv")
    else:
        counts["players"] = 0

    crosswalk_path = processed_dir / "player_id_crosswalk.csv"
    if crosswalk_path.exists():
        cw = pd.read_csv(crosswalk_path)
        map_df = cw[["nba_player_id", "college_player_id", "college_url"]].copy()
        map_df = map_df[map_df["college_player_id"].notna() & map_df["college_url"].notna()]
        counts["nba_college_map"] = _write_csv(map_df, processed_dir / "nba_college_map.csv")
    else:
        counts["nba_college_map"] = 0

    sid_path = season_ids_path or _find_season_ids_csv(raw_dir)
    if sid_path is not None and Path(sid_path).exists():
        appearances = _dedupe_season_appearances(pd.read_csv(sid_path))
        counts["nba_season_appearances"] = _write_csv(
            appearances,
            processed_dir / "nba_season_appearances.csv",
        )
    else:
        counts["nba_season_appearances"] = 0

    nba_long_path = raw_dir / "nba_player_tables_long.csv"
    if nba_long_path.exists():
        nba_long = pd.read_csv(nba_long_path)
        nba_parts = _split_by_table_id(nba_long, id_cols=("nba_player_id",))
        for tid in NBA_TABLE_IDS:
            part = nba_parts.get(tid)
            if part is None or part.empty:
                counts[f"nba_{tid}"] = 0
                continue
            part = _drop_br_spacer_rows(part)
            counts[f"nba_{tid}"] = _write_csv(part, processed_dir / f"nba_{tid}.csv")
    else:
        for tid in NBA_TABLE_IDS:
            counts[f"nba_{tid}"] = 0

    cbb_long_path = raw_dir / "college_player_tables_long.csv"
    if cbb_long_path.exists():
        cbb_long = pd.read_csv(cbb_long_path)
        cbb_parts = _split_by_table_id(
            cbb_long,
            id_cols=("college_player_id", "college_url"),
        )
        for tid in CBB_TABLE_IDS:
            part = cbb_parts.get(tid)
            if part is None or part.empty:
                counts[f"cbb_{tid}"] = 0
                continue
            part = _drop_br_spacer_rows(part)
            counts[f"cbb_{tid}"] = _write_csv(part, processed_dir / f"cbb_{tid}.csv")
    else:
        for tid in CBB_TABLE_IDS:
            counts[f"cbb_{tid}"] = 0

    return counts


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    counts = write_normalized_tables(raw_dir, processed_dir)
    print("Normalized tables written:")
    for name, n in sorted(counts.items()):
        print(f"  {name}: {n} rows")


if __name__ == "__main__":
    main()
