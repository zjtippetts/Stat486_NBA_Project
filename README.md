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
├── notebooks/                # EDA + supervised modeling (e.g. 03_supervised_modeling.ipynb)
├── demo/                     # Deliverable 4 demo: PCA notebook
├── outputs/                  # Generated tables (not milestone prose)
│   ├── supervised/           # e.g. permutation importance CSV
│   └── unsupervised/         # Deliverable 4 tables (PCA loadings, correlations)
└── presentation/             # Final slides (PPTX) + optional generator script
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
   A full pull can take **roughly an hour or more**. If you stop it midway, see **`data/README.md` → “Interrupted `run_data_pull`”** for cleanup / git restore. **Supervised v1** does not require finishing a pull for height/weight.
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
   | Rebuild `model_base` + normalized tables from saved raw CSVs (no scrape) | `python -m src.data.rebuild_model_base` |

   Cleanup logic (deduped season appearances, dropped blank `Season` spacer rows in normalized stat tables, 429 backoff, etc.) lives in `src/data/` and runs automatically on `run_data_pull` or via the commands above.

5. **EDA and supervised modeling**  
   Document workflow in `progress/02_eda.md` and `progress/03_supervised.md`. Supervised models use **college advanced** from each player's **last NCAA season** on `model_base` (see `src/data/run_data_pull.py`), plus **debut age** and **rookie position**. **Ridge, LassoCV, random forest, gradient boosting** (recruiting excluded), **BPM complete-case** filtering. Implementation: **`src/models/evaluate_supervised.py`** (tuning, test metrics, permutation importance); modeling table: **`src/models/training_data.py`**. Run either:  
   ```bash
   python -m src.models.evaluate_supervised
   ```  
   …or **`notebooks/03_supervised_modeling.ipynb`** (same `main()`; demo-friendly). Writes **`outputs/supervised/permutation_importance.csv`**, **`progress/figures/supervised_perm_importance.png`**, and prints a JSON summary. The **markdown report** (`progress/03_supervised.md`) is not auto-updated—edit it if you need prose/tables to match a new run.

6. **PCA (Deliverable 4 — additional ML method)**  
   Wide numeric feature matrix (advanced + per-100 + totals + demographics; **no recruiting**, same as supervised philosophy); **same 595-row cohort and train/test split** as step 5; **impute, scale, and PCA fit on train only**. Writes CSVs under **`outputs/unsupervised/`** and figures **`progress/figures/pca_*.png`**. Run:
   ```bash
   python -m src.models.pca_analysis
   ```
   **Demo artifact for graders:** **`demo/04_pca_deliverable4.ipynb`** (calls the same `main()`). Narrative: **`progress/04_unsupervised.md`**.

7. **Presentation slides (Deliverable 4 / 5)**  
   Prebuilt deck: **`presentation/Stat486_NBA_Final.pptx`**. Regenerate after changing talking points:
   ```bash
   python presentation/generate_slides.py
   ```

---

## Data Sources

- **Basketball-Reference (Sports Reference):** College stats, NBA draft history, NBA career stats.  
  [https://www.basketball-reference.com/](https://www.basketball-reference.com/)

---

## Progress Deliverables

| Deliverable | Status |
|-------------|--------|
| 01 Proposal | ✓ |
| 02 Data & EDA | ✓ |
| 03 Supervised modeling | ✓ (see `03_supervised.md`; re-run script for fresh metrics) |
| 04 Additional ML method | ✓ (`progress/04_unsupervised.md`, `demo/04_pca_deliverable4.ipynb`, `presentation/Stat486_NBA_Final.pptx`) |

---

## Figures and Main Results

| Topic | Location |
| --- | --- |
| EDA | `progress/figures/eda_*.png` |
| Supervised permutation importance (plot) | `progress/figures/supervised_perm_importance.png` |
| Supervised permutation importance (table) | `outputs/supervised/permutation_importance.csv` |
| PCA loadings / PC vs outcome correlations | `outputs/unsupervised/pca_loadings.csv`, `pca_pc_success_correlation.csv` |
| PCA scree / variance | `progress/figures/pca_scree.png`, `pca_cumulative_variance.png` |
| PCA PC1 vs PC2 (train, colored by composite) | `progress/figures/pca_pc1_pc2_train_scatter.png` |
| PCA PC1 loadings | `progress/figures/pca_pc1_loadings_bar.png` |

Re-run **`python -m src.models.evaluate_supervised`** and **`python -m src.models.pca_analysis`** after any change to modeling inputs.
