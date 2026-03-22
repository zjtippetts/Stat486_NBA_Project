# Deliverable 1: Project Proposal

**STAT 486 Final Project — NBA Draft Player Success Prediction**

---

## 1. Candidate Project Ideas (AI-Generated)

Using generative AI to brainstorm within the sports analytics domain, the following candidate ideas emerged:

### Idea A: NBA Draft Player Success Prediction (Selected)
Predict the career success of NBA draft prospects using college statistics and pre-draft combine data. Success is measured by an **aggregated metric** (e.g., composite of counting stats, advanced metrics like Win Shares/VORP, minutes played, etc.) that can be bucketed for classification. Supervised models (regression or classification) predict this outcome. **PCA (dimensionality reduction)** reveals which pre-draft indicators best predict success via loadings and PC–success correlations.

**Data:** College stats and NBA career outcomes from Basketball-Reference (Sports Reference). College-route players only; 10 seasons of draft cohorts.

### Idea B: Draft Position vs. Performance Mismatch
Focus on predicting *mismatches* between draft slot and eventual performance—specifically, flagging players who over- or underperform relative to their draft position. Supervised model predicts a “value delta” (actual performance minus expected given draft slot). Anomaly detection finds outliers (biggest busts and steals) for further analysis.

**Data:** Basketball-Reference draft history and career stats.

### Idea C: Player Archetype Discovery and Success
Use **clustering** first to discover natural player archetypes from college stats and physical measurements. Then use **supervised learning** to predict whether a prospect’s archetype tends to succeed in the NBA. This flips the usual order: archetype membership becomes a feature for the success model.

**Data:** College basketball stats, NBA Combine data, and NBA career outcomes from Sports Reference.

---

## 2. AI Reflection

I used AI to explore project ideas that combine supervised learning with another ML technique in sports analytics. The AI suggested several directions, including draft bust/steal prediction and archetype-based modeling. I found the “aggregated success metric” approach most appealing because it allows flexibility: I can define success in a nuanced way (e.g., combining counting stats, advanced metrics, minutes) and bucket players for regression or classification. When I asked which second technique best reveals which indicators predict success, AI recommended PCA over clustering or anomaly detection—PCA loadings directly show which pre-draft variables matter. I iterated on data scope (10 seasons, college-route players only) and confirmed PCA is approved in the instructions.

---

## 3. Excerpt of AI Exchange

**User:** What would be the best ML concept for the second technique if we want to figure out what indicators best predict the NBA success metric?

**AI (paraphrased):** Dimensionality reduction (PCA) is the best fit. Use PCA on pre-draft features—the loadings tell you which original variables drive each principal component. Correlate PC scores with the success metric to see which dimensions predict success. Clustering groups players into archetypes but is less direct for "which indicators matter." PCA is explicitly approved in the instructions.

---

## 4. Final Research Question

**Can we predict NBA draft prospect career success using college statistics and pre-draft data, and which pre-draft indicators best predict success?**

---

## 5. Candidate Target Variable

**Aggregated success metric** — A composite score combining multiple NBA career statistics, such as:

- Counting statistics (points, rebounds, assists, etc.)
- Advanced metrics (Win Shares, VORP)
- Minutes played (longevity and role)
- All-Star appearances (optional, if available)

The exact formula will be defined during data exploration (e.g., weighted combination or PCA-based composite). This metric can be used for:

- **Regression:** Predict the continuous success score.
- **Classification (optional):** Threshold the metric (e.g., top 25% vs. bottom 75%) for binary or multi-class prediction.

---

## 6. Dataset Choice and Backup

| Source | Primary / Backup | Description |
|--------|------------------|-------------|
| **Basketball-Reference (Sports Reference)** | Primary | College stats, NBA Draft history, NBA career stats, Combine data. Free, well-documented, widely used. All data expected from this source. |
| **NBA.com/Stats** | Backup | Official NBA data if needed. |
| **Kaggle NBA datasets** | Backup | Pre-aggregated draft datasets if retrieval is limited. |

**Scope:** 10 seasons of draft cohorts. All players who played in the NBA (drafted or undrafted) from the college route only; international/professional/overseas prospects excluded. ~700–900 players expected. Retrieval via Basketball-Reference pages and/or Python libraries (`sportsdataverse`, `basketball_reference_scraper`), with exact steps in `data/README.md`.

---

## 7. Feasibility

- **Time:** 4–5 weeks; scope is manageable with clear milestones.
- **Compute:** Draft cohorts are typically hundreds of players per year; no GPU or distributed compute needed.
- **Scope:** One primary dataset, 2–3 supervised models, one additional ML method (PCA). Depth over breadth.

---

## 8. Ethical and Legal Considerations

- **License:** Basketball-Reference permits non-commercial and educational use with attribution. We will cite the source and follow robots.txt / rate-limiting guidelines.
- **Data content:** Performance statistics only; no personally identifiable or sensitive information.
- **Interpretation:** Results will be framed as exploratory analytics, not definitive judgments about individual players.

---

## 9. Planned Additional ML Method

**PCA (Dimensionality Reduction)**  
Apply PCA to pre-draft features (college stats, combine measurements). Loadings reveal which original variables drive each principal component. Correlate PC scores with the aggregated success metric to identify which dimensions of pre-draft performance best predict NBA success. This directly addresses the question of which indicators matter most, complementary to supervised model feature importance (SHAP, permutation importance). Optional: use t-SNE for visualization if helpful.

---

## Checklist (for submission)

- [x] 2–3 AI-generated ideas included
- [x] AI reflection and excerpt included
- [x] Final question and target variable included
- [x] Dataset choice and backup dataset included
