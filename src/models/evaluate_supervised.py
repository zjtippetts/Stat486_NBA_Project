"""
Train ridge, lasso (L1 feature selection), random forest, and gradient boosting
with CV; evaluate on held-out test.
Run: python -m src.models.evaluate_supervised
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LassoCV, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.models.training_data import (
    TARGET_COL,
    build_supervised_frame,
    supervised_feature_columns,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> dict:
    root = _repo_root()
    fig_dir = root / "progress" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    df = build_supervised_frame(require_non_null_bpm=True)
    feat_cols = supervised_feature_columns(df)
    X = df[feat_cols]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    ridge_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", Ridge()),
        ]
    )
    ridge_grid = {"model__alpha": np.logspace(-2, 3, 24)}
    ridge_cv = GridSearchCV(
        ridge_pipe,
        ridge_grid,
        cv=5,
        scoring="neg_root_mean_squared_error",
        n_jobs=-1,
    )
    ridge_cv.fit(X_train, y_train)
    ridge_best = ridge_cv.best_estimator_
    y_pred_r = ridge_best.predict(X_test)

    # --- Lasso (L1): alpha chosen by built-in CV; zeros out uninformative coefficients. ---
    lasso_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LassoCV(cv=5, random_state=42, max_iter=50_000, n_jobs=-1)),
        ]
    )
    lasso_pipe.fit(X_train, y_train)
    lasso_best = lasso_pipe
    y_pred_l = lasso_best.predict(X_test)
    lasso_model = lasso_best.named_steps["model"]
    lasso_coef = np.asarray(lasso_model.coef_).ravel()
    lasso_nz = np.abs(lasso_coef) > 1e-8
    lasso_selected = [feat_cols[i] for i in np.where(lasso_nz)[0]]
    lasso_cv_rmse = float(np.sqrt(np.min(np.mean(lasso_model.mse_path_, axis=1))))

    rf_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestRegressor(random_state=42, n_jobs=-1),
            ),
        ]
    )
    rf_dist = {
        "model__n_estimators": [200, 400, 600],
        "model__max_depth": [4, 6, 8, 12, None],
        "model__min_samples_leaf": [1, 3, 6, 12],
        "model__max_features": ["sqrt", 0.3, 0.6],
    }
    rf_search = RandomizedSearchCV(
        rf_pipe,
        rf_dist,
        n_iter=24,
        cv=5,
        scoring="neg_root_mean_squared_error",
        random_state=42,
        n_jobs=-1,
    )
    rf_search.fit(X_train, y_train)
    rf_best = rf_search.best_estimator_
    y_pred_f = rf_best.predict(X_test)

    # --- Gradient boosting (HistGradientBoosting) ---
    gb_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("model", HistGradientBoostingRegressor(random_state=42)),
        ]
    )
    gb_dist = {
        "model__learning_rate": [0.01, 0.05, 0.1, 0.2],
        "model__max_iter": [100, 200, 400],
        "model__max_depth": [3, 5, 8, None],
        "model__min_samples_leaf": [5, 10, 20],
        "model__l2_regularization": [0.0, 0.1, 1.0],
    }
    gb_search = RandomizedSearchCV(
        gb_pipe,
        gb_dist,
        n_iter=30,
        cv=5,
        scoring="neg_root_mean_squared_error",
        random_state=42,
        n_jobs=-1,
    )
    gb_search.fit(X_train, y_train)
    gb_best = gb_search.best_estimator_
    y_pred_g = gb_best.predict(X_test)

    def metrics(y_true, y_pred) -> dict:
        return {
            "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "r2": float(r2_score(y_true, y_pred)),
        }

    ridge_metrics = metrics(y_test, y_pred_r)
    lasso_metrics = metrics(y_test, y_pred_l)
    rf_metrics = metrics(y_test, y_pred_f)
    gb_metrics = metrics(y_test, y_pred_g)

    out = {
        "n_total": int(len(df)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_features": len(feat_cols),
        "feature_names": feat_cols,
        "ridge": {
            "best_params": {k: float(v) if isinstance(v, (np.floating, float)) else v for k, v in ridge_cv.best_params_.items()},
            "cv_best_rmse": float(-ridge_cv.best_score_),
            "test": ridge_metrics,
        },
        "lasso_cv": {
            "alpha": float(lasso_model.alpha_),
            "cv_best_rmse": lasso_cv_rmse,
            "n_nonzero_coefs": int(np.sum(lasso_nz)),
            "selected_features": lasso_selected,
            "test": lasso_metrics,
        },
        "random_forest": {
            "best_params": _serialize_params(rf_search.best_params_),
            "cv_best_rmse": float(-rf_search.best_score_),
            "test": rf_metrics,
        },
        "gradient_boosting": {
            "best_params": _serialize_params(gb_search.best_params_),
            "cv_best_rmse": float(-gb_search.best_score_),
            "test": gb_metrics,
        },
    }

    all_models = {
        "ridge": (ridge_best, ridge_metrics["r2"]),
        "lasso_cv": (lasso_best, lasso_metrics["r2"]),
        "random_forest": (rf_best, rf_metrics["r2"]),
        "gradient_boosting": (gb_best, gb_metrics["r2"]),
    }
    out["best_test_r2_model"] = max(all_models, key=lambda k: all_models[k][1])

    # Permutation importance: use best among ridge / RF / GB only. Lasso often uses
    # few features; shuffling columns the fit ignored yields near-zero importance for
    # most names, which is misleading for a global "what drives predictions?" plot.
    perm_candidates = {k: all_models[k] for k in ("ridge", "random_forest", "gradient_boosting")}
    best_name = max(perm_candidates, key=lambda k: perm_candidates[k][1])
    best_estimator = perm_candidates[best_name][0]

    perm = permutation_importance(
        best_estimator,
        X_test,
        y_test,
        n_repeats=25,
        random_state=42,
        n_jobs=-1,
    )
    imp = pd.Series(perm.importances_mean, index=feat_cols).sort_values(ascending=False)
    out["permutation_importance_model"] = best_name
    out["permutation_importance_excludes_lasso_cv"] = True
    out["permutation_importance_top10"] = imp.head(10).round(5).to_dict()

    imp_tbl = (
        pd.DataFrame(
            {
                "feature": feat_cols,
                "importance_mean": perm.importances_mean,
                "importance_std": perm.importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )
    imp_path = root / "progress" / "permutation_importance.csv"
    imp_tbl.to_csv(imp_path, index=False)
    out["permutation_importance_csv"] = str(imp_path.relative_to(root)).replace("\\", "/")

    try:
        import matplotlib.pyplot as plt

        pretty = best_name.replace("_", " ")
        fig, ax = plt.subplots(figsize=(8, 5))
        top = imp.head(12).sort_values(ascending=True)
        top.plot(kind="barh", ax=ax, color="steelblue")
        ax.set_title(f"Permutation importance ({pretty}, test set)")
        fig.tight_layout()
        fig.savefig(fig_dir / "supervised_perm_importance.png", dpi=150)
        plt.close()
        out["figure"] = "progress/figures/supervised_perm_importance.png"
    except ImportError:
        out["figure"] = None

    print(json.dumps(out, indent=2))
    return out


def _serialize_params(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if v is None:
            out[k] = None
        elif isinstance(v, (np.integer, int)):
            out[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            out[k] = float(v)
        else:
            out[k] = str(v)
    return out


if __name__ == "__main__":
    main()
