"""
Rebuild ``data/processed/model_base_player_season.csv`` from saved raw CSVs.

Use after changing merge logic (e.g. college season selection) without re-scraping.
Requires: ``data/raw/nba_player_tables_long.csv``,
``data/raw/college_player_tables_long.csv``, ``data/processed/player_id_crosswalk.csv``.

Run: python -m src.data.rebuild_model_base
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.normalize_tables import write_normalized_tables
from src.data.run_data_pull import _build_model_base_player_season, _repo_root


def main() -> None:
    root = _repo_root()
    raw_dir = root / "data" / "raw"
    proc_dir = root / "data" / "processed"

    nba_path = raw_dir / "nba_player_tables_long.csv"
    cbb_path = raw_dir / "college_player_tables_long.csv"
    cw_path = proc_dir / "player_id_crosswalk.csv"
    season_path = raw_dir / "nba_season_player_ids_2011_2025.csv"

    for p in (nba_path, cbb_path, cw_path):
        if not p.exists():
            raise FileNotFoundError(f"Missing required file: {p}")

    nba_long = pd.read_csv(nba_path)
    crosswalk = pd.read_csv(cw_path)
    college_long = pd.read_csv(cbb_path)

    model_base = _build_model_base_player_season(nba_long, crosswalk, college_long)
    out_path = proc_dir / "model_base_player_season.csv"
    model_base.to_csv(out_path, index=False)
    print(f"Wrote {len(model_base)} rows -> {out_path.relative_to(root)}")

    season_ids_path = season_path if season_path.exists() else None
    norm = write_normalized_tables(raw_dir, proc_dir, season_ids_path=season_ids_path)
    print("Normalized tables:", {k: v for k, v in norm.items() if v})


if __name__ == "__main__":
    main()
