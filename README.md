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
├── requirements.txt          # Python dependencies (to be added)
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

3. **Obtain data**  
   Follow instructions in `data/README.md` to download or fetch data from Basketball-Reference.

4. **Run scripts in order**  
   (To be documented as workflows are built: data prep → EDA → modeling → evaluation.)

---

## Data Sources

- **Basketball-Reference (Sports Reference):** College stats, NBA draft history, NBA career stats.  
  [https://www.basketball-reference.com/](https://www.basketball-reference.com/)

---

## Progress Deliverables

| Deliverable | Status |
|-------------|--------|
| 01 Proposal | ✓ |
| 02 Data & EDA | Pending |
| 03 Supervised modeling | Pending |
| 04 Additional ML method | Pending |

---

## Figures and Main Results

(To be added as the project progresses.)
