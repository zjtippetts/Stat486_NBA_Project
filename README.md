# NBA Draft Player Success Prediction

**STAT 486 Final Project — Winter/Spring 2026**

---

## Project Overview

This project uses machine learning to predict NBA draft prospect career success using college statistics and pre-draft data from Sports Reference (Basketball-Reference). We build supervised models to predict an aggregated success metric and use PCA (dimensionality reduction) to identify which pre-draft indicators best predict success. Scope: 10 seasons of draft cohorts; college-route players only.

**Research question:** Can we predict NBA draft prospect career success using college statistics and pre-draft data, and which pre-draft indicators best predict success?

---

## Repository Structure

```
Stat486_NBA_Project/
├── README.md                 # This file
├── instructions.md           # Course project instructions
├── requirements.txt          # Python dependencies
│
├── data/                     # Data storage and access
│   ├── README.md             # Data sources, retrieval instructions
│   ├── raw/                  # Raw data from Basketball-Reference
│   └── processed/            # Cleaned datasets for modeling
│
├── src/                      # Reproducibility scripts
│   ├── data/                 # Data fetching and preprocessing
│   ├── models/               # Supervised and additional ML code
│   └── utils/                # Shared utilities
│
├── progress/                 # Milestone reports
│   ├── 01_proposal.md        # Deliverable 1: Proposal
│   ├── 02_eda.md             # Deliverable 2: Data and EDA
│   ├── target_variable_spec.md  # Locked outcome definition (v1)
│   ├── 03_supervised.md      # Deliverable 3: Supervised modeling
│   └── 04_unsupervised.md    # Deliverable 4: Additional ML method
│
├── notebooks/                # Jupyter notebooks (EDA, demos)
└── demo/                     # Demo artifact (.ipynb or Streamlit app)
```

---

## Steps to Reproduce

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Stat486_NBA_Project
   ```

2. **Create environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Pull NBA + college data** (writes `data/raw/*`, crosswalk, `model_base_player_season.csv`, normalized tables, summaries)
   ```bash
   python -m src.data.run_data_pull
   ```
   Optional quick validation run (smaller sample):
   ```bash
   python -c "from src.data.run_data_pull import run_data_pull; run_data_pull(start_season=2025, end_season=2025, max_players=25)"
   ```

4. **Optional follow-ups** (same machine, no full re-scrape unless noted)  
   Full command reference: [`data/README.md`](data/README.md).

   | Step | Command |
   |------|---------|
   | Rebuild normalized CSVs from current raw files | `python -m src.data.normalize_tables` |
   | Retry NBA pages listed in `scrape_failures.csv` | `python -m src.data.retry_failed_nba` |
   | Backfill missing college rows for crosswalk slugs | `python -m src.data.backfill_college` |
   | Validation counts / summary | `python -m src.data.validate_data` |
   | Integrity checks | `python -m src.data.validate_data --readiness` |
   | Refresh `scrape_summary.csv` from disk | `python -m src.data.validate_data --refresh-summary` |
   | Duplicate / empty-row audit | `python -m src.data.csv_audit` |
   | Repair `scrape_failures.csv` from profiles | `python -m src.data.validate_data --repair-failures` |

   Cleanup logic (deduped season appearances, dropped blank `Season` spacer rows in normalized stat tables, 429 backoff, etc.) lives in `src/data/` and runs automatically on `run_data_pull` or via the commands above.

5. **EDA and modeling**  
   Document workflow and choices in `progress/02_eda.md` and following deliverables; use `data/processed/` tables or `model_base_player_season.csv` as inputs.

---

## Data Sources

- **Basketball-Reference (Sports Reference):** College stats, NBA draft history, NBA career stats.  
  [https://www.basketball-reference.com/](https://www.basketball-reference.com/)

---

## Progress Deliverables

| Deliverable | Status |
|-------------|--------|
| 01 Proposal | ✓ |
| 02 Data & EDA | Ready for submission (final review) |
| 03 Supervised modeling | Pending |
| 04 Additional ML method | Pending |

---

## Figures and Main Results

(To be added as the project progresses.)
