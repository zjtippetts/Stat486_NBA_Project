"""
PCA on a wide pre-NBA feature set (Deliverable 4).

Fits ``SimpleImputer`` → ``StandardScaler`` → ``PCA`` on the **training** split only
(same ``random_state`` and test fraction as ``evaluate_supervised``), then transforms
train and test for plots and correlations.

Run: python -m src.models.pca_analysis

Tabular outputs go under ``outputs/unsupervised/``; figures under ``progress/figures/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.models.training_data import (
    DEMOGRAPHIC_FEATURE_COLS,
    TARGET_COL,
    build_modeling_cohort_frame,
)

# Broader than supervised v1 (advanced-only): totals and per-100 (no recruiting).
_CBB_PREFIXES = ("cbb_advanced_", "cbb_per100_", "cbb_totals_")
_MAX_MISSING_FRAC = 0.5
_TEST_SIZE = 0.2
_RANDOM_STATE = 42
# Retain enough components for interpretability while capturing most variance.
_PCA_VARIANCE = 0.90


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def select_pca_feature_columns(df: pd.DataFrame) -> list[str]:
    """Numeric columns: college blocks + demographics (matches supervised: no recruiting)."""
    candidates: list[str] = []
    for c in df.columns:
        if c in (TARGET_COL, "nba_player_id"):
            continue
        if any(c.startswith(p) for p in _CBB_PREFIXES):
            candidates.append(c)
        elif c in DEMOGRAPHIC_FEATURE_COLS:
            candidates.append(c)

    usable: list[str] = []
    for c in sorted(set(candidates)):
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        miss = s.isna().mean()
        if miss > _MAX_MISSING_FRAC:
            continue
        v = s.dropna()
        if v.empty or v.nunique() <= 1:
            continue
        usable.append(c)
    return usable


def main() -> dict:
    root = _repo_root()
    fig_dir = root / "progress" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    out_dir = root / "outputs" / "unsupervised"
    out_dir.mkdir(parents=True, exist_ok=True)

    cohort = build_modeling_cohort_frame(require_non_null_bpm=True)
    feat_cols = select_pca_feature_columns(cohort)
    if len(feat_cols) < 3:
        raise ValueError(f"Too few PCA features after filtering: {feat_cols}")

    X = cohort[feat_cols].apply(pd.to_numeric, errors="coerce")
    y = cohort[TARGET_COL].astype(float)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=_TEST_SIZE,
        random_state=_RANDOM_STATE,
    )

    prep = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    X_train_t = prep.fit_transform(X_train)
    X_test_t = prep.transform(X_test)

    # Float in (0, 1): keep the smallest k with cumulative explained variance >= target.
    pca = PCA(n_components=_PCA_VARIANCE, svd_solver="full")
    pca.fit(X_train_t)
    Z_train = pca.transform(X_train_t)
    Z_test = pca.transform(X_test_t)

    evr = pca.explained_variance_ratio_
    cum = np.cumsum(evr)

    loadings = pd.DataFrame(
        pca.components_.T,
        index=feat_cols,
        columns=[f"PC{i + 1}" for i in range(pca.n_components_)],
    )
    load_path = out_dir / "pca_loadings.csv"
    loadings.to_csv(load_path)

    # Pearson correlation between each PC and outcome (train / test).
    pc_names = [f"PC{i + 1}" for i in range(pca.n_components_)]
    corr_rows = []
    for split_name, Z, yt in (
        ("train", Z_train, y_train),
        ("test", Z_test, y_test),
    ):
        for j, name in enumerate(pc_names):
            r = np.corrcoef(Z[:, j], yt.values)[0, 1]
            corr_rows.append({"split": split_name, "pc": name, "r_success": float(r)})
    corr_df = pd.DataFrame(corr_rows)
    corr_path = out_dir / "pca_pc_success_correlation.csv"
    corr_df.to_csv(corr_path, index=False)

    # --- Figures ---
    sns.set_theme(style="whitegrid", context="talk")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(np.arange(1, len(evr) + 1), evr, color="steelblue", alpha=0.85)
    ax.set_xlabel("Principal component")
    ax.set_ylabel("Explained variance ratio")
    ax.set_title("PCA scree (fit on training split only)")
    fig.tight_layout()
    fig.savefig(fig_dir / "pca_scree.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(np.arange(1, len(cum) + 1), cum, marker="o", color="darkred")
    ax.axhline(_PCA_VARIANCE, color="gray", linestyle="--", label=f"{_PCA_VARIANCE:.0%} variance")
    ax.set_xlabel("Number of components")
    ax.set_ylabel("Cumulative explained variance")
    ax.set_title("PCA cumulative variance (train)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "pca_cumulative_variance.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    sc = ax.scatter(
        Z_train[:, 0],
        Z_train[:, 1],
        c=y_train.values,
        cmap="RdYlGn",
        alpha=0.70,
        edgecolors="k",
        linewidths=0.3,
        s=30,
    )
    plt.colorbar(sc, ax=ax, label=TARGET_COL)
    ax.set_xlabel("PC1 (train)")
    ax.set_ylabel("PC2 (train)")
    ax.set_title("Training players: PC1 vs PC2 colored by success composite")
    fig.tight_layout()
    fig.savefig(fig_dir / "pca_pc1_pc2_train_scatter.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # De-duplicate: many features measure the same stat across blocks
    # (e.g. cbb_advanced_ORBpct, cbb_per100_ORB, cbb_totals_ORB).
    # Show one bar per base stat using the variant with the largest |loading|.
    pc1_all = loadings["PC1"]
    base_map: dict[str, tuple[str, float]] = {}
    for feat, val in pc1_all.items():
        for prefix in (*_CBB_PREFIXES, "pos_is_", "nba_debut_"):
            if feat.startswith(prefix):
                base = feat[len(prefix):]
                break
        else:
            base = feat
        if base not in base_map or abs(val) > abs(base_map[base][1]):
            base_map[base] = (feat, val)
    deduped = pd.Series(
        {base: val for base, (_, val) in base_map.items()}
    )
    top_k = min(12, len(deduped))
    pc1_top = deduped.reindex(deduped.abs().nlargest(top_k).index)
    fig, ax = plt.subplots(figsize=(8, 5))
    pc1_top.sort_values().plot(kind="barh", ax=ax, color="teal", alpha=0.85)
    ax.set_xlabel("Loading on PC1 (best variant per base stat)")
    ax.set_title(f"Top {top_k} base stats on PC1 (de-duplicated, train fit)")
    fig.tight_layout()
    fig.savefig(fig_dir / "pca_pc1_loadings_bar.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "n_players": int(len(cohort)),
        "n_features_pca": len(feat_cols),
        "n_components": int(pca.n_components_),
        "cumulative_variance_last_pc": float(cum[-1]),
        "train_test_split": {"test_size": _TEST_SIZE, "random_state": _RANDOM_STATE},
        "pca_target_variance": _PCA_VARIANCE,
        "feature_columns": feat_cols,
        "artifacts": {
            "loadings_csv": str(load_path.relative_to(root)).replace("\\", "/"),
            "correlations_csv": str(corr_path.relative_to(root)).replace("\\", "/"),
            "figures": [
                "progress/figures/pca_scree.png",
                "progress/figures/pca_cumulative_variance.png",
                "progress/figures/pca_pc1_pc2_train_scatter.png",
                "progress/figures/pca_pc1_loadings_bar.png",
            ],
        },
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
