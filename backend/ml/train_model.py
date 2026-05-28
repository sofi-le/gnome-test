"""
G-Nome Elastic Net Model Trainer
=================================
Trains per-disease LogisticRegression models with ElasticNet penalty using
cross-validated hyperparameter search over L1 ratio and regularization strength.

Usage:
    python -m ml.train_model

Output:
    backend/ml/models.joblib — dict of {disease_name: trained_model}
"""

import os
import warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from ml.snp_config import ALL_SNPS, DISEASES, DISEASE_DISPLAY_NAMES

# Suppress convergence and deprecation warnings during grid search
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Feature columns: all SNP rsIDs + ancestry weight
FEATURE_COLS = ALL_SNPS + ["ancestry_weight"]

# Hyperparameter grid for ElasticNet logistic regression
# Uses the sklearn 1.8+ API: l1_ratio controls L1/L2 mix, C controls strength
PARAM_GRID = {
    "classifier__l1_ratio": [0.1, 0.3, 0.5, 0.7, 0.9],
    "classifier__C": [0.01, 0.1, 1.0, 10.0],
}


def _build_pipeline() -> Pipeline:
    """
    Build a sklearn pipeline with standard scaling and ElasticNet
    logistic regression.

    Uses solver='saga' which supports elastic net via l1_ratio.
    The l1_ratio is set via GridSearchCV param_grid.
    """
    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            solver="saga",
            l1_ratio=0.5,  # Default; overridden by grid search
            max_iter=5000,
            random_state=42,
            class_weight="balanced",  # Handle imbalanced classes
        )),
    ])


def train_models(
    data_path: str | None = None,
    output_path: str | None = None,
) -> dict:
    """
    Train one ElasticNet logistic regression per disease.

    Returns:
        dict mapping disease name → {
            "model": trained Pipeline,
            "best_params": dict,
            "cv_score": float,
            "feature_names": list[str],
            "non_zero_features": list[str],
            "coefficients": dict[str, float],
        }
    """
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), "synthetic_training_data.csv")

    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "models.joblib")

    print(f"Loading training data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Dataset: {df.shape[0]} samples, {df.shape[1]} columns\n")

    X = df[FEATURE_COLS].values
    results = {}

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for disease in DISEASES:
        label_col = f"label_{disease}"
        y = df[label_col].values

        print(f"{'='*60}")
        print(f"Training model for: {DISEASE_DISPLAY_NAMES[disease]}")
        print(f"  Positive samples: {y.sum()}/{len(y)} ({y.mean():.1%})")

        pipeline = _build_pipeline()

        grid_search = GridSearchCV(
            pipeline,
            PARAM_GRID,
            cv=cv,
            scoring="roc_auc",
            n_jobs=-1,
            verbose=0,
            refit=True,
        )

        grid_search.fit(X, y)

        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        best_score = grid_search.best_score_

        # Extract coefficients from the logistic regression step
        classifier = best_model.named_steps["classifier"]
        coefficients = classifier.coef_[0]

        # Identify non-zero coefficient features (selected by L1)
        non_zero_mask = np.abs(coefficients) > 1e-6
        non_zero_features = [
            FEATURE_COLS[i] for i in range(len(FEATURE_COLS)) if non_zero_mask[i]
        ]
        coef_dict = {
            FEATURE_COLS[i]: float(coefficients[i])
            for i in range(len(FEATURE_COLS))
            if non_zero_mask[i]
        }

        # Sort by absolute coefficient value
        coef_dict = dict(sorted(
            coef_dict.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        ))

        results[disease] = {
            "model": best_model,
            "best_params": best_params,
            "cv_score": best_score,
            "feature_names": FEATURE_COLS,
            "non_zero_features": non_zero_features,
            "coefficients": coef_dict,
        }

        print(f"  Best params: C={best_params['classifier__C']}, "
              f"l1_ratio={best_params['classifier__l1_ratio']}")
        print(f"  CV ROC-AUC: {best_score:.4f}")
        print(f"  Non-zero features ({len(non_zero_features)}/{len(FEATURE_COLS)}):")
        for feat, coef in coef_dict.items():
            direction = "↑ risk" if coef > 0 else "↓ risk"
            print(f"    {feat:>15s}: {coef:+.4f}  ({direction})")
        print()

    # Serialize all models
    joblib.dump(results, output_path)
    print(f"{'='*60}")
    print(f"All models saved to: {output_path}")

    return results


if __name__ == "__main__":
    train_models()
