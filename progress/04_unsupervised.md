# Deliverable 4: Additional ML method (PCA)

**STAT 486 - dimensionality reduction on the same cohort as supervised learning**

---

## Method

PCA is a natural fit here because the **80** college features are **heavily collinear**: many stats appear as advanced rates, per-100 rates, and raw totals of the same underlying box-score number. Supervised models already mitigate collinearity (**Ridge** shrinks correlated coefficients; **Lasso** drops redundant terms; **trees** split on one feature at a time). PCA complements them by making which **directions of variation** exist in the wide matrix explicit, so we can interpret geometry and relate component scores to career success.

The feature set is `cbb_advanced_*`, `cbb_per100_*`, `cbb_totals_*`, **`nba_debut_age`**, and rookie **position dummies** (no recruiting). Rows match supervised modeling (**595** players). Same **80/20** split (`random_state=42`); **median imputation** and **standardization** fit on **train only**, then PCA on the scaled train matrix. **scikit-learn** kept components until **90%** train variance (**13** PCs from **80** features). Run: `python -m src.models.pca_analysis`.

## New insight beyond supervised analysis

Supervised models highlighted a **short** list of drivers (**age**, **BPM**, **DBPM**) while shrinking many collinear rates. PCA shows **why**: most stats sit on a few shared axes. **PC1** loads on **rebounding** (ORB%, TRB%) with **negative** weight on **three-point attempt rate** -- a **role** contrast (interior vs perimeter), not a single quality axis. Regressions do not show that role geometry as clearly. PC-success correlations stay fairly **weak** (PC1 about **0.14** on train), matching supervised **R-squared** near **0.15**: PCA organizes variance but does not unlock stronger prediction.

## Conclusion

PCA complements supervision by collapsing collinear pre-draft stats into **interpretable** axes (here, rebounding versus outside shot mix) while regressions emphasize a few advanced rates. Both point to **weak** composite signal and **strong** multicollinearity. Next steps: regress on a **small** PC set with the same split, or **cluster** PC scores into archetypes.

---

**Reproduction:** `python -m src.models.pca_analysis` | Demo: `demo/04_pca_deliverable4.ipynb`
