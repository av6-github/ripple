"""Tests for Quantitative Signal Backtesting & Information Coefficient (IC) Analysis."""

import numpy as np
import pandas as pd
from backend.quant.backtesting import SignalEvaluator


def test_signal_backtest_evaluates_predictive_power():
    """Verify Information Coefficient, Rank IC, and AUC metrics on predictive signal."""
    np.random.seed(42)
    n = 150

    # Synthetic risk driver: higher leverage -> higher default rate
    true_latent_risk = np.random.normal(0, 1, n)
    leverage_signal = true_latent_risk + np.random.normal(0, 0.5, n)
    prob_default = 1.0 / (1.0 + np.exp(-true_latent_risk))
    default_outcomes = (prob_default > 0.6).astype(int)

    sig_s = pd.Series(leverage_signal, name="leverage_signal")
    tgt_s = pd.Series(default_outcomes, name="default_flag")

    res = SignalEvaluator.evaluate_signal(
        signal_series=sig_s,
        target_series=tgt_s,
        signal_name="Debt / Assets",
    )

    assert res.sample_size == n
    assert res.rank_ic > 0.30  # Strong positive Rank IC with default
    assert res.is_statistically_significant is True
    assert res.p_value < 0.01
    assert res.enhanced_auc > 0.70
    assert res.signal_direction == "positive_risk"
    assert "Statistically significant" in res.evaluation_summary


def test_uninformative_noise_signal_fails_significance():
    """Verify pure white noise signal has zero statistical significance."""
    np.random.seed(123)
    n = 100
    noise_signal = pd.Series(np.random.normal(0, 1, n))
    outcomes = pd.Series(np.random.choice([0, 1], size=n, p=[0.8, 0.2]))

    res = SignalEvaluator.evaluate_signal(
        signal_series=noise_signal,
        target_series=outcomes,
        signal_name="Random Gaussian Noise",
    )

    assert abs(res.rank_ic) < 0.20
    assert res.is_statistically_significant is False
