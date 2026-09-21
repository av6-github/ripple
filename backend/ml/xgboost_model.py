"""XGBoost tabular risk model for Polish Companies Bankruptcy prediction."""

from typing import Any, Dict, Optional
import xgboost as xgb


def create_xgboost_model(
    scale_pos_weight: float = 13.4,
    max_depth: int = 4,
    learning_rate: float = 0.05,
    n_estimators: int = 150,
    subsample: float = 0.8,
    colsample_bytree: float = 0.8,
    random_state: int = 42,
    **kwargs: Any,
) -> xgb.XGBClassifier:
    """Create tuned XGBoost classifier for imbalanced credit default prediction."""
    return xgb.XGBClassifier(
        scale_pos_weight=scale_pos_weight,
        max_depth=max_depth,
        learning_rate=learning_rate,
        n_estimators=n_estimators,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        eval_metric="logloss",
        random_state=random_state,
        n_jobs=-1,
        **kwargs,
    )
