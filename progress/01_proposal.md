# Deliverable 1: Project Proposal

**STAT 486 Final Project — NBA Draft Player Success Prediction**

---

## 1. Candidate Project Ideas (AI-Generated)

I used generative AI to brainstorm ideas in sports analytics. These are the three directions it suggested:

### Idea A: NBA Draft Player Success Prediction (Selected)
Predict how successful NBA draft prospects become using college stats and pre-draft data (for example combine numbers). **Success** is one combined score built from NBA career stats (box score stats, advanced stats like Win Shares or VORP, games played, and similar). I can use that score in **regression** or bucket it for **classification**. I will also use **PCA** on the pre-draft features. PCA loadings and correlations with the success score help show which inputs matter most.

**Data:** College and NBA stats from Basketball-Reference (Sports Reference). College-route players only, about 10 seasons of draft-related cohorts.

### Idea B: Draft Position vs. Performance Mismatch
Predict how far a player ends up above or below what you would expect from their draft slot. Flag big over- and under-performers. Could add anomaly-style analysis on the errors.

**Data:** Basketball-Reference draft history and career stats.

### Idea C: Player Archetype Discovery and Success
Use **clustering** on college stats and physical measures to form player types. Then use **supervised learning** to see whether some types tend to succeed more in the NBA.

**Data:** College stats, combine-style data, and NBA outcomes from Sports Reference.

---

## 2. AI Reflection

I used AI to find project paths that pair **supervised learning** with a **second ML method**. It suggested several ideas, including bust/steal style work and archetype-based modeling. I picked the **single success score** approach because I can define success in one clear way (mix of stats and longevity) and still use regression or classification. I asked which second method best answers “which indicators predict success?” The AI pointed to **PCA** over clustering or anomaly detection: loadings tie PCs back to original variables, and I can correlate PC scores with the outcome. I narrowed scope to about 10 seasons and college-route players only, and I checked that PCA is allowed in the course instructions.

---

## 3. Excerpt of AI Exchange

**Me:** What would be the best ML concept for a second technique if I want to see which indicators best predict my NBA success metric?

**AI (paraphrased):** Use **dimensionality reduction (PCA)**. Fit PCA on pre-draft features. Loadings show which variables drive each component. Correlate component scores with the success metric to see what predicts success. Clustering groups players but is less direct for “which variables matter.” PCA fits the instructions.

---

## 4. Final Research Question

**Can I predict NBA draft prospect career success using college statistics and pre-draft data, and which pre-draft indicators best predict success?**

---

## 5. Candidate Target Variable

**One combined success score** built from NBA career information, such as:

- Box score stats (points, rebounds, assists, etc.)
- Advanced stats (Win Shares, VORP)
- Games played (longevity and role)
- All-Star counts (optional if easy to add)

I will pin down the exact formula during EDA (for example a weighted mix). I can use it for:

- **Regression:** Predict the continuous score.
- **Classification (optional):** Split into high vs low groups (for example top quarter vs bottom quarter).

---

## 6. Dataset Choice and Backup

| Source | Primary / Backup | Description |
|--------|------------------|-------------|
| **Basketball-Reference (Sports Reference)** | Primary | College stats, draft-related pages, NBA career stats, combine-style fields. Free and widely used. I plan to pull most data from here. |
| **NBA.com/Stats** | Backup | Official NBA stats if I need them. |
| **Kaggle NBA datasets** | Backup | Ready-made tables if scraping is too limited. |

**Scope:** About 10 seasons of draft-related cohorts. Players who reached the NBA on the college path (drafted or not). I am not focusing on international-only prospects. I expect on the order of hundreds to about 900 players, depending on filters. Steps and file layout are in `data/README.md`.

---

## 7. Feasibility

- **Time:** About 4–5 weeks; the plan is focused and fits the term.
- **Compute:** Cohort sizes are modest; I do not need a GPU or distributed setup.
- **Scope:** One main data pipeline, 2–3 supervised models, and PCA as the extra method. I am prioritizing depth over adding many extra tasks.

---

## 8. Ethical and Legal Considerations

- **Use of the site:** Basketball-Reference allows educational and non-commercial use with credit. I will cite the source and respect robots.txt and rate limits when scraping.
- **What the data contain:** Game and player performance stats only, not sensitive personal data.
- **How I will present results:** As exploratory analysis, not as final labels on real people.

---

## 9. Planned Additional ML Method

**PCA (dimensionality reduction)**  
I will run PCA on college and pre-draft features. Loadings show which original variables push each component. I will relate component scores to my success metric to see which directions in the data track NBA success. This pairs with supervised model tools like feature importance or SHAP. I might add t-SNE plots only if they help explain the story.

**Note on supervised models (Deliverable 3):** My first regression models in `progress/03_supervised.md` use **college advanced stats only** (no recruiting), with rows dropped when college **BPM** is missing. PCA can still draw on a **broader** set of columns where that fits the question.

---

## Checklist (for submission)

- [x] 2–3 AI-generated ideas included
- [x] AI reflection and excerpt included
- [x] Final question and target variable included
- [x] Dataset choice and backup dataset included
