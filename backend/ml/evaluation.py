"""Evaluation and ablation metrics for tabular credit risk models.

Computes:
- ROC-AUC (Discrimination)
- PR-AUC / Average Precision (Class imbalance performance)
- Kolmogorov-Smirnov (KS) Statistic (Credit risk industry standard)
- Brier Score & Expected Calibration Error
- Precision, Recall, F1
"""

from typing import Any, Dict
import numpy as np
from scipy.stats import ks_2samp
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from backend.ml.calibrator import calculate_expected_calibration_error


def calculate_ks_statistic(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Calculate the two-sample Kolmogorov-Smirnov (KS) statistic between default and non-default scores."""
    defaults = y_prob[y_true == 1]
    non_defaults = y_prob[y_true == 0]
    if len(defaults) == 0 or len(non_defaults) == 0:
        return 0.0
    ks_res = ks_2samp(defaults, non_defaults)
    return float(round(ks_res.statistic, 4))


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, float]:
    """Compute comprehensive credit-risk evaluation metrics on a test set."""
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    else:
        y_prob = model.predict(X_test)

    y_pred = (y_prob >= threshold).astype(int)

    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    brier = float(brier_score_loss(y_test, y_prob))
    ece = calculate_expected_calibration_error(y_test, y_prob)
    ks_stat = calculate_ks_statistic(y_test, y_prob)

    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "ks_statistic": round(ks_stat, 4),
        "brier_score": round(brier, 6),
        "expected_calibration_error": round(ece, 6),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
    }
