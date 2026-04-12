# Data Directory

## Project: NBA Draft Player Success Prediction

This directory holds data used for the STAT 486 final project. All data are sourced from **Sports Reference** (Basketball-Reference + Sports-Reference CBB pages). Current scraping scope is NBA seasons **2011-2025** from league totals pages, then player-level NBA and college pages linked from those players.

---

## Data Sources

### Primary: Basketball-Reference (Sports Reference)

- **URL:** https://www.basketball-reference.com/
- **License:** Non-commercial and educational use permitted with proper attribution.
- **Citation:** Basketball-Reference.com. Retrieved [date]. https://www.basketball-reference.com/

### Relevant pages used by scraper

| Data type | URL / page |
|-----------|------------|
| NBA season player list | `/leagues/NBA_YYYY_totals.html` for `YYYY=2011..2025` |
| NBA player profile + tables | `/players/<letter>/<nba_player_id>.html` |
| College player profile + tables | `https://www.sports-reference.com/cbb/players/<college_player_id>.html` |

---

## Retrieval Instructions

Run the automated scraper:

```bash
python -m src.data.run_data_pull
```

Optional quick test run:

```bash
python -c "from src.data.run_data_pull import run_data_pull; run_data_pull(start_season=2025, end_season=2025, max_players=25)"
```

Rebuild **normalized** tables from existing raw CSVs (no re-scrape):

```bash
python -m src.data.normalize_tables
```

Quick **validation report** (counts, failures, missing college links, table_id coverage):

```bash
python -m src.data.validate_data
```

**CSV audit** (empty rows, key duplicates, exact duplicates; explains known BR quirks):

```bash
python -m src.data.csv_audit
```

**Integrity checks** (season list vs profiles, crosswalk vs college long, etc.):

```bash
python -m src.data.validate_data --readiness
```

**Refresh `scrape_summary.csv`** after a retry or manual edits (no scraping):

```bash
python -m src.data.validate_data --refresh-summary
```

**Backfill college tables** for any `college_player_id` in the crosswalk that still has no rows in `college_player_tables_long.csv` (can take a while; use `--max-workers 2` if you see 429s):

```bash
python -m src.data.backfill_college
python -m src.data.backfill_college --max-workers 2
```

Progress is logged to stderr every 25 completed pages by default (`--progress-every N`; use `--progress-every 0` for every page). Pass `--quiet` to suppress those lines.

If `scrape_failures.csv` is empty but `nba_player_profile_fields.csv` shows `scrape_status == error`, rebuild the log from profiles (NBA rows only):

```bash
python -m src.data.validate_data --repair-failures
```

**HTTP 429 failures** (rate limiting) are common when many player pages are fetched in parallel. The scraper now waits longer on 429 and uses fewer concurrent requests by default. To **re-try only failed NBA URLs** from `scrape_failures.csv`, merge results, refresh college rows for newly fixed players, and rebuild processed files:

```bash
python -m src.data.retry_failed_nba
python -m src.data.retry_failed_nba --max-workers 2
```

(Run when you are not in a hurry; use `--max-workers 2` or `1` if you still see 429s.)

**Rebuild `model_base` only** (no HTTP): after changing how college rows are merged (e.g. last season vs career), refresh `model_base_player_season.csv` and normalized splits from existing raw CSVs:

```bash
python -m src.data.rebuild_model_base
```

Requires `data/raw/nba_player_tables_long.csv`, `data/raw/college_player_tables_long.csv`, and `data/processed/player_id_crosswalk.csv`.

---

## Interrupted `run_data_pull`

If you **stop** a full pull partway through:

- **`data/raw/`** (`nba_player_profile_fields.csv`, `nba_player_tables_long.csv`, `college_player_tables_long.csv`, …) and **`data/processed/model_base_player_season.csv`** may be **partial or inconsistent** until you finish a clean run.
- **Restore known-good processed files** with git when needed, e.g.  
  `git checkout -- data/processed/model_base_player_season.csv`  
  (and any other paths that look truncated), **or** let a **full** pull complete when you have time (often **45 min–several hours**).
- **Deliverable 2 (EDA):** Re-run outcome/college notebooks only if you **intentionally** changed `model_base` or `player_career_summary_v1.csv` and want figures to match. An aborted pull does not by itself require redoing EDA if you **revert** processed data.
- **Deliverable 3:** Run `python -m src.models.evaluate_supervised` after any change to the modeling inputs. **Supervised v1** does **not** depend on a completed pull for height/weight — it uses **debut age** and **rookie `Pos`** from existing `model_base` plus college advanced (see `src/models/training_data.py`).

---

## Output files

**Raw** (scraper output; long-format stat tables are convenient for debugging but wide/sparse when opened):

```
data/
├── raw/
│   ├── nba_season_player_ids_2011_2025.csv
│   ├── nba_player_profile_fields.csv
│   ├── nba_player_tables_long.csv
│   ├── college_player_tables_long.csv
│   ├── scrape_summary.csv
│   └── scrape_failures.csv
└── processed/
    ├── player_id_crosswalk.csv
    └── model_base_player_season.csv
```

**Normalized** (database-style; one file per stat family, no cross-table column union). Produced automatically at the end of `run_data_pull`, or via `python -m src.data.normalize_tables`:

| File | Role |
|------|------|
| `players.csv` | Reference: NBA profile/bio fields from the scrape |
| `nba_college_map.csv` | Reference: `nba_player_id` → `college_player_id` / `college_url` (players with a college link only) |
| `nba_season_appearances.csv` | Reference: one row per **(season, nba_player_id)** (duplicates from multi-team stints on league totals pages are dropped when building this file) |
| `nba_totals.csv`, `nba_per100.csv`, `nba_advanced.csv`, `nba_adj_shooting.csv`, `nba_shooting.csv` | NBA stat blocks; grain follows Basketball-Reference (multiple rows per season if traded, plus career/summary rows BR includes) |
| `nba_play_by_play.csv` | Present when the play-by-play block is available on the player page (may be empty) |
| `cbb_totals.csv`, `cbb_per100.csv`, `cbb_advanced.csv` | College stat blocks keyed by `college_player_id` |

Join keys: `nba_player_id` within NBA tables; `nba_college_map` links to `cbb_*` via `college_player_id`.

---

## Data scope

- Seasons scraped: **2011 through 2025**
- Inclusion: all players listed on NBA season totals pages
- Missing info handling: if college link/recruiting rank/tables are missing, keep player rows and leave nullable fields
- Mapping key: `nba_player_id` linked to `college_player_id` (derived from college URL)

## Data size

- College + NBA career stats: text/CSV; total size expected &lt; 50 MB.

---

## Preprocessing baked into the pipeline (reproducible in code)

- **League player list:** `run_data_pull` saves `nba_season_player_ids_*.csv` with **one row per (season, nba_player_id)** (multi-team stints on BR are collapsed).
- **Normalized outputs:** `normalize_tables` writes **`nba_season_appearances.csv`** deduped the same way, and drops **blank `Season` spacer rows** from NBA/CBB stat splits when writing `nba_*.csv` / `cbb_*.csv`.
- **HTTP 429:** longer waits and retries in `utils.fetch_html`; lower default concurrency on profile/college scrapes.
- Re-run **`normalize_tables`** anytime to regenerate processed files from current raw CSVs without scraping.

## Notes

- Respect rate limits when scraping; reruns may take substantial time for full-player pulls.
- Store raw data locally; do not re-scrape unnecessarily.
- Document EDA choices in `progress/02_eda.md`. **Supervised modeling (Deliverable 3)** filters and features are in `progress/03_supervised.md` and `src/models/training_data.py` (**`nba_debut_age`**, **rookie NBA position dummies** from `Pos`, college **`cbb_advanced_*`**, **no recruiting**, **complete case on college BPM**; height/weight optional for future pulls only). Permutation-importance table: `outputs/supervised/permutation_importance.csv`.
