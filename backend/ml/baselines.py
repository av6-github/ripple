"""Baseline machine learning models for Polish Bankruptcy risk prediction.

Implements standard benchmark baselines:
- Regularized Logistic Regression with class-imbalance reweighting
- Random Forest Classifier with balanced subsampling
"""

from typing import Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def create_logistic_regression_baseline(
    random_state: int = 42,
    c_val: float = 1.0,
    max_iter: int = 1000,
) -> Pipeline:
    """Create scaled Logistic Regression baseline pipeline with balanced weights."""
    return Pipeline([
        ("scaler", StandardScaler()),
        (
            "classifier",
            LogisticRegression(
                C=c_val,
                class_weight="balanced",
                max_iter=max_iter,
                random_state=random_state,
                solver="lbfgs",
            ),
        ),
    ])


def create_random_forest_baseline(
    random_state: int = 42,
    n_estimators: int = 100,
    max_depth: Optional[int] = 8,
) -> RandomForestClassifier:
    """Create Random Forest baseline classifier with balanced bootstrap subsamples."""
    return RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )
