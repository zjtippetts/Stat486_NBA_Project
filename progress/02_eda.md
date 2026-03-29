# Deliverable 2: Data and EDA

**STAT 486 — NBA success from college and pre-draft data**

This is my Data and EDA write-up: what I built, what I measured, plots I made, and what was hard. Full outcome rules are in `progress/target_variable_spec.md`. I did the work in `notebooks/02_eda_outcomes.ipynb`, `notebooks/02_eda_college.ipynb`, and `src/analysis/career_outcomes.py`.

---

## 1) Research question and dataset overview

**Research question.** Can I predict NBA career success for college-route players using college stats and pre-draft information, and which pre-draft inputs matter most? (I stated this in `progress/01_proposal.md`.)

**What I built.** I scraped **Basketball-Reference** for NBA season totals and advanced stats and **Sports Reference college** for career college tables. I merged them into `data/processed/model_base_player_season.csv`. Each row is one NBA player-season. College career fields are the same for every season row for that player. I also saved `data/processed/player_career_summary_v1.csv` with one row per NBA player and my outcome fields.

**Credit.** Data come from [Basketball-Reference](https://www.basketball-reference.com/) and [Sports Reference / College Basketball](https://www.sports-reference.com/cbb/). I use them for class work, give credit in the repo, and throttle requests in my scrapers.

**Ethics.** The tables are public stats and basic bio fields. I do not use private or sensitive data. Beyond citing the source and scraping politely, I do not see an extra ethical issue for this project.

---

## 2) Data description, target variable, and preprocessing

**Outcome I plan to predict later.** I call it `success_composite_v1`. It applies only to players whose **first NBA season** is between **2011–12** and **2022–23** (my **entry cohort**) and who have **tier D**: at least **two** seasons with **G ≥ 10** and **MP ≥ 100** (my **qualifying** seasons). The score is **0.55 × z(mean fantasy points per game in qualifying seasons) + 0.45 × z(log(1 + career games))**. Fantasy points follow a fixed box-score recipe in `target_variable_spec.md`. Players in tiers **B** and **C** do not get this score; I kept them in the summary for counts and context.

**Inputs (pre-NBA).** Columns starting with `cbb_totals_`, `cbb_per100_`, and `cbb_advanced_` (for example college PER and BPM), plus `recruiting_rank` and `recruiting_year` when they exist. In `02_eda_college.ipynb` I focused on the subset with tier **D**, entry cohort, a non-null `college_player_id`, and a non-null composite—that is the sample I can use later for supervised learning with both sides filled in.

**What I did to clean the data.** (1) For each player-season, I kept one NBA row; when a combined multi-team row (`2TM` / `3TM`) was present, I kept that row so I would not double-count. (2) I marked qualifying seasons using the G and MP rules above. (3) I rolled up to one career row per player, assigned tiers, and computed the composite where the rules apply. (4) For college summaries I collapsed to one row per `nba_player_id`. Recruiting fields were often missing; I report those gaps in section 3.

---

## 3) Summary statistics and relationships

**Career summary file (`player_career_summary_v1.csv`).** **1,812** players. **Tier counts:** **B = 305**, **C = 237**, **D = 1,270**. (In my extract no one is tier A; everyone has at least one minute recorded as games played.) **1,128** players are in the entry cohort. **713** have a non-null `success_composite_v1` (tier D and cohort).

**Composite (713 players).** Mean is about **0** and standard deviation about **0.91** because of the z-score step. Min about **−1.81**, max about **2.94**.

**College-focused modeling slice (611 players):** tier D, cohort, college id, and non-null composite. College **PER:** 602 non-null values, mean **21.3**, SD **4.5**, median **20.8**. College **BPM:** 595 non-null, mean **6.9**, SD **2.7**. **Recruiting rank:** 360 non-null, mean **33.1**, SD **28.1**, median **24.5** (smaller rank means more highly ranked recruit).

**Correlations.** In `02_eda_college.ipynb` I correlated selected college fields with `success_composite_v1`. The heatmap is `progress/figures/eda_cbb_feature_correlation.png`. College PER and the composite correlated about **0.28** in that run—useful signal, but not tight enough to predict one player perfectly.

**Takeaway.** The outcome spans a couple of standard deviations on the composite scale. College advanced stats help on average but leave a lot of noise. Recruiting rank is missing for many players; even when it is there, it only partly lines up with my NBA success score.

---

## 4) Visual exploration

All plots are in `progress/figures/`. Here is what each one is for.

**NBA outcomes (`02_eda_outcomes.ipynb`).**


| Figure                           | What it shows                                 | Why it matters for my question                                                           |
| -------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `eda_tier_career_games.png`      | Career games by tier B/C/D.                   | Shows how many players had a short NBA run vs a long one, and who even gets a composite. |
| `eda_success_composite_hist.png` | Histogram of `success_composite_v1`.          | Shows the shape of the outcome I want to predict later.                                  |
| `eda_fp_vs_career_games.png`     | Mean fantasy points per game vs career games. | Shows how scoring rate and longevity relate; my outcome mixes both.                      |
| `eda_z_correlation.png`          | Fantasy z-score vs longevity z-score.         | Shows whether stars are high on both parts or only one.                                  |


**College side (`02_eda_college.ipynb`).**


| Figure                             | What it shows                                         | Why it matters for my question                                                          |
| ---------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `eda_cbb_missingness.png`          | Share missing for key college and recruiting columns. | Tells me which features I can trust for modeling; recruiting is especially spotty.      |
| `eda_cbb_per_distribution.png`     | College PER for the modeling slice.                   | Shows the main college skill summary I will use with other `cbb_*` fields.              |
| `eda_cbb_recruit_vs_composite.png` | Recruit rank vs composite when both exist.            | Checks whether hype lines up with my NBA score; expect scatter.                         |
| `eda_cbb_feature_correlation.png`  | Correlation heatmap.                                  | Quick view of how inputs relate to each other and to the outcome before PCA and models. |


---

## 5) Challenges and reflection

The hardest part was **scraping**: rate limits, a few bad pages, and many players with **no college URL** (on the order of **~300** in the project notes), so they have no `cbb_*` block. I treated them separately in EDA and will only train with players who have college data. **Active players** also have careers that are not finished, so games played will grow over time. I do **not** adjust fantasy points for NBA era; the score can mix real skill with league-wide scoring trends. I write that down instead of changing the v1 rule for this deliverable.

---

## Limitations (for later modeling)

**Era.** Fantasy points per game use raw stats. The NBA scoring environment changes over time, so the outcome is not “era-neutral.”

**Tier D only.** Models fit on `success_composite_v1` only learn from players who reached **two** qualifying seasons. A low prediction does **not** mean “will wash out” unless I add a separate model for that. Details are in `target_variable_spec.md`.

**Other.** The composite is a teaching and analysis choice, not a claim about “true” player value. Some shooting breakdown columns are not filled in `model_base` in my current merge; I can use separate shooting CSVs if I need them.

---

## Submission checklist (Deliverable 2)

- This file: overview, variables, preprocessing, numbers, correlations, plots explained, reflection.  
- Notebooks: `notebooks/02_eda_outcomes.ipynb`, `notebooks/02_eda_college.ipynb`.  
- Figures in `progress/figures/` (re-run notebooks if I change code).  
- Canvas: repo link and note *Deliverable 2 complete* when I submit.

