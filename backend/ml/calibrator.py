"""Probability calibration and reliability evaluation for tabular risk models.

Implements:
- Platt Sigmoid and Isotonic Regression calibration via CalibratedClassifierCV
- Brier Score calculation
- Expected Calibration Error (ECE) measurement
- Strict validation that calibrated outputs lie in [0.0, 1.0] (MODEL-003)
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss


def calculate_expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Calculate Expected Calibration Error (ECE) across probability bins."""
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)

    for i in range(n_bins):
        bin_lower = bin_edges[i]
        bin_upper = bin_edges[i + 1]
        
        # Include upper boundary on the last bin
        if i == n_bins - 1:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
            
        bin_size = np.sum(in_bin)
        if bin_size > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_prob[in_bin])
            ece += (bin_size / total_samples) * abs(bin_acc - bin_conf)

    return float(round(ece, 6))


class ProbabilityCalibrator:
    """Fits and applies probability calibration to base estimators."""

    def __init__(self, method: str = "isotonic", cv: int = 5) -> None:
        if method not in ("isotonic", "sigmoid"):
            raise ValueError(f"Unknown calibration method: {method}. Allowed: 'isotonic', 'sigmoid'")
        self.method = method
        self.cv = cv
        self.calibrated_model_: Optional[CalibratedClassifierCV] = None

    def fit(self, base_estimator: Any, X: np.ndarray, y: np.ndarray) -> "ProbabilityCalibrator":
        """Fit calibrated model using cross-validation on training data."""
        self.calibrated_model_ = CalibratedClassifierCV(
            estimator=base_estimator,
            method=self.method,
            cv=self.cv,
        )
        self.calibrated_model_.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict calibrated default probabilities strictly bounded in [0.0, 1.0]."""
        if self.calibrated_model_ is None:
            raise RuntimeError("Calibrator not fitted. Call fit() first.")
        probas = self.calibrated_model_.predict_proba(X)
        # Bounded assurance
        return np.clip(probas, 0.0, 1.0)

    def evaluate_calibration(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        n_bins: int = 10,
    ) -> Dict[str, float]:
        """Compute Brier Score, ECE, and reliability curve points."""
        brier = float(brier_score_loss(y_true, y_prob))
        ece = calculate_expected_calibration_error(y_true, y_prob, n_bins=n_bins)
        
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
        
        return {
            "brier_score": round(brier, 6),
            "expected_calibration_error": round(ece, 6),
            "prob_true": [round(float(x), 4) for x in prob_true],
            "prob_pred": [round(float(x), 4) for x in prob_pred],
        }
