"""Quantitative Signal Processing & Transformation Suite for RIPPLE.

Implements institutional investment-R&D signal engineering:
1. Winsorisation & Outlier Controls (1st - 99th percentile truncation)
2. Cross-Sectional Ranking (NACE sector percentile normalization in [0, 1])
3. Rolling & Expanding Risk Metrics (Rolling Volatility, Expanding Min, Max Drawdown)
4. Feature Neutralisation (OLS projection to eliminate Sector and Size/Log-Asset confounding)
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


def winsorize_series(
    series: pd.Series,
    lower_quantile: float = 0.01,
    upper_quantile: float = 0.99,
) -> pd.Series:
    """Cap extreme distribution tails at specified quantiles to prevent ratio blowups.

    Parameters
    ----------
    series : pd.Series
        Raw continuous financial ratio.
    lower_quantile : float
        Lower clipping threshold (default 1st percentile).
    upper_quantile : float
        Upper clipping threshold (default 99th percentile).

    Returns
    -------
    pd.Series
        Winsorized series with clipped bounds.
    """
    valid = series.dropna()
    if len(valid) == 0:
        return series.copy()

    lower_val = valid.quantile(lower_quantile)
    upper_val = valid.quantile(upper_quantile)

    return series.clip(lower=lower_val, upper=upper_val)


def winsorize_dataset(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    lower_quantile: float = 0.01,
    upper_quantile: float = 0.99,
) -> Tuple[pd.DataFrame, Dict[str, Tuple[float, float]]]:
    """Winsorize multiple feature columns and return clipping boundaries for auditability."""
    res_df = df.copy()
    target_cols = columns or [c for c in df.select_dtypes(include=[np.number]).columns]
    bounds: Dict[str, Tuple[float, float]] = {}

    for col in target_cols:
        if col in res_df.columns:
            valid = res_df[col].dropna()
            if len(valid) > 0:
                low = float(valid.quantile(lower_quantile))
                high = float(valid.quantile(upper_quantile))
                res_df[col] = res_df[col].clip(lower=low, upper=high)
                bounds[col] = (round(low, 4), round(high, 4))

    return res_df, bounds


def cross_sectional_percentile_rank(
    df: pd.DataFrame,
    feature_cols: List[str],
    group_col: Optional[str] = "nace_sector",
) -> pd.DataFrame:
    """Transform continuous financial ratios into uniform percentile ranks in [0.0, 1.0].

    If `group_col` is provided and present in the dataframe, ranks are computed
    within each industry cohort (sector-relative normalization). Otherwise,
    ranks are computed across the entire cohort.
    """
    ranked_df = df.copy()

    for col in feature_cols:
        if col not in ranked_df.columns:
            continue

        rank_col_name = f"{col}_pct_rank"

        if group_col and group_col in ranked_df.columns:
            # Group-wise ranking: (rank - 1) / (N - 1) or pct=True
            ranked_df[rank_col_name] = ranked_df.groupby(group_col)[col].rank(
                pct=True, method="average"
            )
        else:
            ranked_df[rank_col_name] = ranked_df[col].rank(pct=True, method="average")

        # Fill any remaining NaNs with neutral 0.5 (median rank)
        ranked_df[rank_col_name] = ranked_df[rank_col_name].fillna(0.5)

    return ranked_df


def compute_rolling_expanding_metrics(
    series: pd.Series,
    window: int = 3,
) -> pd.DataFrame:
    """Compute rolling volatility, expanding historical minimum, and maximum drawdown.

    Parameters
    ----------
    series : pd.Series
        Historical time-ordered corporate metric (e.g. quarterly operating cash flows).
    window : int
        Rolling window length (default 3 periods).

    Returns
    -------
    pd.DataFrame
        DataFrame containing `rolling_volatility`, `expanding_min`, and `max_drawdown`.
    """
    s = series.astype(float).copy()

    # 1. Rolling Volatility (Sample Standard Deviation over window)
    rolling_vol = s.rolling(window=window, min_periods=2).std().fillna(0.0)

    # 2. Expanding Minimum (Liquidity headroom / worst historical stress)
    expanding_min = s.expanding(min_periods=1).min()

    # 3. Maximum Drawdown (Relative drop from expanding historical peak)
    expanding_peak = s.expanding(min_periods=1).max()
    drawdown = (s - expanding_peak) / expanding_peak.replace(0, np.nan)
    drawdown = drawdown.fillna(0.0)
    # Drawdown is expressed as a positive percentage drop (e.g. 0.25 = 25% peak-to-trough decline)
    max_drawdown = (-drawdown).clip(lower=0.0)

    return pd.DataFrame(
        {
            "rolling_volatility": rolling_vol.round(4),
            "expanding_min": expanding_min.round(2),
            "max_drawdown": max_drawdown.round(4),
        },
        index=series.index,
    )


def neutralize_features(
    signal: pd.Series,
    exposures: pd.DataFrame,
) -> pd.Series:
    """Neutralize a financial signal against structural risk factors (e.g. sector dummies, log-assets).

    Performs an Ordinary Least Squares (OLS) cross-sectional regression:
        $$\\text{signal} = X \\beta + \\epsilon$$
    and extracts the residual vector $\\epsilon$, guaranteeing zero linear correlation
    with the exposure matrix $X$.
    """
    # Clean aligned valid indices
    common_idx = signal.dropna().index.intersection(exposures.dropna().index)
    if len(common_idx) < exposures.shape[1] + 2:
        # Insufficient degrees of freedom: return demeaned signal
        return signal - signal.mean()

    y = signal.loc[common_idx].values.astype(float)
    X = exposures.loc[common_idx].copy()

    # Add intercept column if not present
    if "const" not in X.columns:
        X["const"] = 1.0

    X_mat = X.values.astype(float)

    # Solve OLS via least squares: beta = (X^T X)^-1 X^T y
    try:
        beta, residuals, rank, s = np.linalg.lstsq(X_mat, y, rcond=None)
        fitted = X_mat @ beta
        resid = y - fitted
        return pd.Series(resid, index=common_idx, name=f"{signal.name}_neutralized")
    except Exception:
        # Fallback to simple demean
        return signal - signal.mean()
