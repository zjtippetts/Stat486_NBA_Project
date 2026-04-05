# Target variable and analysis frame (v1) — **LOCKED**

This document locks **definitions** for EDA (Deliverable 2) and later supervised modeling. Refinements go here as `v1.1`, `v2`, etc.

---

## 1. Research question (unchanged)

**Can we predict NBA career success from pre-NBA (college) information, and which indicators matter most?**  
(See `progress/01_proposal.md` for full wording and PCA plan.)

---

## 2. Grain and data source

| Choice | v1 decision |
|--------|-------------|
| **Outcome grain** | One **career summary row per `nba_player_id`** (aggregate from `model_base_player_season.csv` season rows). |
| **Season input file** | `data/processed/model_base_player_season.csv` — NBA totals + merged advanced (`VORP`, `PER`, `BPM`, `WS`, …) + crosswalk + `cbb_*` from each player's **last NCAA season** (not SR **Career** row; same values repeated on every NBA season row for that player). |
| **Features for modeling (later)** | **Deliverable 3 (v1):** **`nba_debut_age`** (birthday + first NBA season), **rookie NBA position dummies** (from `Pos` on earliest deduped season), plus college **`cbb_advanced_*`** only, with **complete case on `cbb_advanced_BPM`**. Recruiting is **not** in the supervised set (sparse—see EDA). `cbb_totals_*` / `cbb_per100_*` are omitted to limit collinearity. **Height/weight** are not required for v1 (optional raw profile fields after a full pull). Recruiting and other `cbb_*` blocks remain in `model_base` for EDA and **v1.1** / PCA. |

### 2.1 One row per player–season (required before any sum or mean)

Many seasons have **multiple rows** (one team + `2TM` / `3TM` / `4TM` combined row). **~1,285** `(nba_player_id, Season)` keys repeat in the current file.

**Rule (locked):** For each `(nba_player_id, Season)`, keep **exactly one** row:

- If any `Team` value matches **`^\d+TM$`** (e.g. `2TM`, `3TM`), **keep only that row** (season totals).  
- Otherwise keep the **single** team row.

All **qualifying-season** checks, **`FP`**, **`G`**, **`MP`**, and **`career_games`** use this deduped season table. **Do not** sum across team stints + `2TM` in the same season.

---

## 3. Fantasy-style productivity index (NBA, season-level)

**Name (for writing):** custom fantasy-style points index, **not** official NBA fantasy.

**Per-season raw index** (using Basketball-Reference naming: `FG` = field goals made):

```
FP = 1*PTS + 1*3P - 1*FGA + 2*FG - 1*FTA + 1*FT + 1*TRB + 2*AST + 4*STL + 4*BLK - 2*TOV
```

**Columns in `model_base_player_season.csv`:** `PTS`, `3P`, `FGA`, `FG`, `FTA`, `FT`, `TRB`, `AST`, `STL`, `BLK`, `TOV`.

**Per-season rate (v1):**

- `FP_per_game = FP / G` (requires `G > 0`; rows with missing `G`/`MP` are already dropped in pipeline).

**Career aggregation (v1):**

- Restrict to **qualifying seasons** only (section 4).
- **Career mean FP per game:** `mean(FP_per_game)` over qualifying seasons.  
  (Alternative later: `sum(FP) / sum(G)` over those same seasons.)

**Optional v1.1 — prime:** mean `FP_per_game` over the **best 3 qualifying seasons** (by `FP_per_game`), or blend 50% career mean / 50% prime mean.

---

## 4. Season eligibility (qualifying seasons) — **LOCKED**

Rows in `model_base_player_season.csv` already require non-null `G` and `MP`. For **rates and means** (fantasy), use **qualifying seasons**:

| Rule | v1 (locked) |
|------|-------------|
| Min games | **`G >= 10`** |
| Min minutes | **`MP >= 100`** in that season |

Both must hold. No extra `MP/G` rule for v1 (keeps the rule simple).

*Rationale:* screens out cup-of-coffee seasons so `FP_per_game` is not driven by 2–5 game samples.

---

## 4.1 NBA “run” tiers (EDA + interpretation) — **LOCKED**

These tiers separate **never really played**, **fringe run**, and **enough sample for the primary score**. Compute from **all** `model_base_player_season` rows for the player **after** applying the **entry cohort** filter (section 10.1).

| Tier | Definition | Use |
|------|------------|-----|
| **A — No stat line** | Player not in `model_base_player_season.csv` **or** `sum(G) == 0` across their rows. | True “no NBA minutes in our tables” (rare if they only appear elsewhere). |
| **B — Fringe run** | `sum(G) >= 1` but **zero** qualifying seasons (section 4). | Got on the floor, never hit 10 games **and** 100 minutes in a season. |
| **C — Single qualifying year** | Exactly **one** qualifying season. | Describe separately; **excluded** from primary composite (noisy one-year rate). |
| **D — Primary score eligible** | **≥ 2** qualifying seasons. | Gets **career mean FP/game**, **longevity**, and final composite. |

**Longevity (locked):**

- **`career_games`:** `sum(G)` over **all** that player’s rows in the analysis window (not only qualifying seasons), so **fringe** players still show small totals vs **never played**.

**Fantasy mean** uses **only qualifying** seasons; **`career_games`** uses **all** rows so “a little run” vs “never” stays visible in EDA.

---

## 5. Success composite (NBA) — **two parts only**

No VORP, DWS, or other advanced index in the outcome — **simpler to explain** and avoids double-counting box stats. Advanced columns on `model_base` remain available for optional EDA plots only.

| Component | Definition | Notes |
|-----------|------------|-------|
| **A. Box fantasy** | z-scored **mean `FP_per_game`** over qualifying seasons | Tier **D** + entry cohort only. |
| **B. Longevity (opportunity-adjusted)** | z-scored **`log(1 + r)`** where **`r = career_games / (eligible_seasons × 82)`** | Same eligibility (tier D + cohort). |

**Opportunity denominator (locked with v1 composite):**

- **`longevity_window_end_year`:** latest season start year present in deduped `model_base_player_season` (e.g. `2024` for `2024-25`).  
- **`eligible_seasons`:** inclusive count of NBA seasons from **`first_season_start_year`** through that end year, at least **1** (only defined when debut year parses as **1990 … window_end**).  
- **`r`** is the share of **nominal** regular-season games (**82** per eligible season) actually played; **lockout / COVID-shortened seasons are not** rescaled (document in limitations).

**Blend weights (sum to 1):**

- `w_A = 0.70` (fantasy career mean)  
- `w_B = 0.30` (longevity)

*Rationale (v1):* weight **per-game box productivity** higher so players who are **very impactful when on the floor** are not pulled down as harshly by a **low games-played share**; durability still matters (e.g. separates ironmen from part-time high-per-minute guys).

**Optional v1.1:** revisit split (e.g. 0.65/0.35) or add a third pillar (e.g. prime-season FP).

---

## 6. Z-scores — **LOCKED**

- **Reference population for z-scoring the composite:** all **tier D** players (section 4.1) in the **entry cohort** (section 10.1).  
- **College-only sensitivity (v1.1):** re-z within `college_player_id` not null if cross-cohort spread dominates.

---

## 7. Modeling cohort vs EDA cohort

| Population | Use |
|------------|-----|
| **EDA** | Full scraped sample; report **tier A/B/C/D** counts; missingness for `cbb_*`. |
| **Supervised v1** | **Tier D** + **entry cohort** + **college id** + non-null composite; **features:** `nba_debut_age` + rookie **`Pos`** dummies + `cbb_advanced_*`, **BPM** complete-case, **no recruiting** (`src/models/training_data.py`). |

---

## 8. Known limitations (document in EDA)

- **Active players:** `career_games` (and thus longevity) are **censored**; the opportunity denominator still runs through the latest season in the scrape, so recent debuts have a smaller denominator.  
- **82 games/year** is a **nominal** schedule; shortened seasons inflate **`r`** slightly for players who played “every” game that year.  
- **~288 players** without `college_url` — no `cbb_*`; exclude or analyze separately.  
- **Shooting-by-distance / `Shooting_*` / `League-Adjusted_*` / dunk & corner columns** in model base are **all empty** in the current pipeline — those tables were **never merged** into `model_base` (only totals + advanced are). Use `nba_shooting.csv` / `nba_adj_shooting.csv` in the notebook if you need them; absence in model base is **not** a scrape failure.

---

## 9. EDA notebook checklist (complete)

- [x] Section 4 min `G` / `MP` locked.  
- [x] Section 4.1 run tiers + longevity aggregation rules.  
- [x] Blend weights stated (may tweak after plots).  
- [x] Z-score reference = tier D + entry cohort.  
- [x] Target: **continuous** + optional **high/low** class (section 10.3).

---

## 10. Cohort and target type — **LOCKED**

### 10.1 Entry cohort (12 NBA “first seasons”)

- **Rule:** Include players whose **first** NBA season in `model_base_player_season.csv` is one of **`2011-12` through `2022-23`** (inclusive).  
- **Implementation:** parse `Season` start year (e.g. `2011-12` → `2011`); require **`2011 <= first_season_start <= 2022`**.  
- **Rationale:** Extends the original 10-season window by **two** years for more sample; trades slightly **more censoring** for very recent debuts (shorter observed careers). Use **2023-24+** debuts as a holdout or v2 sensitivity cohort if needed.

### 10.2 Minimum qualifying seasons for primary composite

- **≥ 2** qualifying seasons (**tier D**).  
- Players in **tier B or C** stay in EDA (run vs fringe vs one-year wonders); they do **not** receive the primary continuous composite (set missing or report side metrics only).

### 10.3 Regression vs classification

- **Primary:** **continuous** composite (section 5).  
- **Secondary (for plots / optional models):** **binary or top/bottom quartile** within tier D + cohort (e.g. success = composite ≥ 75th percentile vs ≤ 25th). Document which percentiles in `02_eda.md`.

---

## 11. Summary table (quick reference)

| Item | Choice |
|------|--------|
| Qualifying season | `G >= 10` and `MP >= 100` |
| Primary composite | Tier **D** only (≥2 qualifying seasons) |
| Entry cohort | First season `2011-12` … `2022-23` |
| Target | Continuous + optional quartile class |
| Composite | 0.70·z(fantasy mean) + 0.30·z(log(1+r)); **r** = games / (eligible seasons × 82); no VORP/DWS |
| Run tiers | A no line / B fringe / C one year / D primary |
