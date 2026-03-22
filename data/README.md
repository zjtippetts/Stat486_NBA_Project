# Data Directory

## Project: NBA Draft Player Success Prediction

This directory holds data used for the STAT 486 final project. All data are sourced from **Sports Reference** (Basketball-Reference). Scope: 10 seasons of draft cohorts; college-route players only (drafted or undrafted who played in the NBA).

---

## Data Sources

### Primary: Basketball-Reference (Sports Reference)

- **URL:** https://www.basketball-reference.com/
- **License:** Non-commercial and educational use permitted with proper attribution.
- **Citation:** Basketball-Reference.com. Retrieved [date]. https://www.basketball-reference.com/

### Relevant pages

| Data type | URL / page |
|-----------|------------|
| NBA Draft history | `/draft/NBA_YYYY.html` (10 seasons, e.g., 2010–2019) |
| College stats | Individual player pages, or `/play-index/draft_finder.cgi` |
| NBA career stats | Player pages under `/players/` |
| NBA Combine | `/draft/combine.html` (if available) |

---

## Retrieval Instructions

Data can be obtained via:

1. **Python libraries**
   - `basketball_reference_scraper` — draft data, player stats
   - `sportsdataverse` (formerly sportsreference) — alternative for NBA/college data

2. **Manual export**
   - Basketball-Reference provides CSV export for many tables via "Share & more" → "Get table as CSV"

3. **Scripts**
   - `src/data/fetch_data.py` (or similar) — will be added to automate retrieval and save outputs to `data/raw/`

---

## Directory structure (planned)

```
data/
├── README.md          # This file
├── raw/               # Raw downloads from Basketball-Reference
├── processed/         # Cleaned, merged datasets for modeling
└── .gitignore         # Ignore large files if needed
```

---

## Data scope

- **10 seasons** of draft cohorts (e.g., 2010–2019 or 2011–2020)
- **College-route players only** — drafted or undrafted, but must have played in the NBA; international/professional/overseas prospects excluded
- ~700–900 players expected

## Data size

- College + NBA career stats: text/CSV; total size expected &lt; 50 MB.

---

## Notes

- Respect rate limits when scraping; add small delays between requests.
- Store raw data locally; do not re-scrape unnecessarily.
- Document any preprocessing steps in `progress/02_eda.md`.
