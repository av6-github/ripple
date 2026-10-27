"""Tests for Quant Signal Processing: Winsorisation, Cross-Sectional Ranking, Rolling Volatility, and Neutralization."""

import numpy as np
import pandas as pd
import pytest
from backend.quant.signals import (
    compute_rolling_expanding_metrics,
    cross_sectional_percentile_rank,
    neutralize_features,
    winsorize_dataset,
    winsorize_series,
)


def test_winsorize_series_caps_extreme_outliers():
    """Verify that extreme ratio outliers (e.g. 100,000 leverage) are truncated to percentiles."""
    raw = [1.0, 1.2, 1.1, 0.9, 1.3, 1.05, 0.95, 1.15, 1.0, 100000.0, -5000.0]
    s = pd.Series(raw)

    winsorized = winsorize_series(s, lower_quantile=0.10, upper_quantile=0.90)

    assert winsorized.max() < 100000.0
    assert winsorized.min() > -5000.0
    assert len(winsorized) == len(s)


def test_winsorize_dataset():
    """Verify dataset winsorization and bounds tracking."""
    df = pd.DataFrame(
        {
            "debt_to_assets": [0.2, 0.3, 0.4, 0.35, 999.0],
            "profit_margin": [0.1, 0.12, 0.08, 0.11, -50.0],
        }
    )

    clean_df, bounds = winsorize_dataset(df, lower_quantile=0.10, upper_quantile=0.90)
    assert clean_df["debt_to_assets"].max() < 999.0
    assert clean_df["profit_margin"].min() > -50.0
    assert "debt_to_assets" in bounds
    assert "profit_margin" in bounds


def test_cross_sectional_percentile_rank():
    """Verify ranking produces uniform percentiles within sectors."""
    df = pd.DataFrame(
        {
            "sme_id": ["A", "B", "C", "D"],
            "nace_sector": ["tech", "tech", "manufacturing", "manufacturing"],
            "ebitda_margin": [0.30, 0.10, 0.08, 0.02],
        }
    )

    ranked = cross_sectional_percentile_rank(df, feature_cols=["ebitda_margin"], group_col="nace_sector")

    assert "ebitda_margin_pct_rank" in ranked.columns
    # In tech, A (0.30) > B (0.10) => rank A > rank B
    tech_a = ranked.loc[ranked["sme_id"] == "A", "ebitda_margin_pct_rank"].values[0]
    tech_b = ranked.loc[ranked["sme_id"] == "B", "ebitda_margin_pct_rank"].values[0]
    assert tech_a > tech_b

    # In manufacturing, C (0.08) > D (0.02) => rank C > rank D
    mfg_c = ranked.loc[ranked["sme_id"] == "C", "ebitda_margin_pct_rank"].values[0]
    mfg_d = ranked.loc[ranked["sme_id"] == "D", "ebitda_margin_pct_rank"].values[0]
    assert mfg_c > mfg_d


def test_compute_rolling_expanding_metrics():
    """Verify multi-period cash flow volatility and drawdown calculations."""
    cash_flows = pd.Series([100.0, 120.0, 80.0, 60.0, 110.0])

    metrics = compute_rolling_expanding_metrics(cash_flows, window=3)

    assert "rolling_volatility" in metrics.columns
    assert "expanding_min" in metrics.columns
    assert "max_drawdown" in metrics.columns

    # Period 4 is 60.0, which is the expanding minimum of the series up to t=4
    assert metrics.loc[3, "expanding_min"] == 60.0

    # Drawdown from peak (120) to trough (60) is (120-60)/120 = 50% = 0.50
    assert metrics.loc[3, "max_drawdown"] == 0.50


def test_neutralize_features():
    """Verify OLS residualization eliminates correlation with exposure factors."""
    np.random.seed(42)
    n = 100
    log_assets = np.random.normal(10, 2, n)
    exposures = pd.DataFrame({"log_assets": log_assets})

    # Raw signal strongly correlated with size
    raw_signal = pd.Series(2.5 * log_assets + np.random.normal(0, 1, n), name="raw_alpha")

    neutral = neutralize_features(raw_signal, exposures)

    # Correlation between neutralized signal and log_assets must be essentially zero (< 1e-10)
    corr = np.corrcoef(neutral.values, log_assets)[0, 1]
    assert abs(corr) < 1e-6
