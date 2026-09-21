"""Authoritative Efficiency, Trend, and Growth calculations for RIPPLE.

Implements SRS FR-04 and Polish Bankruptcy alignment:
- DSO, DPO, DIO, Cash Conversion Cycle, Asset Turnover
- YoY Sales Growth, Revenue Volatility, Margin Trend, Cash Flow Volatility
- Insufficient periods handling
"""

import math
import statistics
from typing import Dict, List, Optional, Tuple
from backend.features.domain import FinancialStatementPeriod
from backend.features.financial_ratios import safe_div


def compute_efficiency_ratios(
    period: FinancialStatementPeriod,
) -> Dict[str, Optional[float]]:
    """Compute operating efficiency and working capital cycle metrics for a single period."""
    features: Dict[str, Optional[float]] = {}

    rev = period.total_revenue
    cogs = period.cost_of_goods_sold if period.cost_of_goods_sold is not None else rev
    ar = period.accounts_receivable
    ap = period.accounts_payable
    inv = period.inventory
    ta = period.total_assets

    # 1. DSO (Days Sales Outstanding) = (AR * 365) / Revenue
    if ar is not None and rev is not None:
        if abs(rev) < 1e-9:
            features["dso"] = 365.0 if ar > 0 else 0.0
        else:
            features["dso"] = safe_div(ar * 365.0, rev, default=None, min_val=0.0, max_val=730.0)
    else:
        features["dso"] = None

    # 2. DPO (Days Payables Outstanding) = (AP * 365) / COGS
    if ap is not None and cogs is not None:
        if abs(cogs) < 1e-9:
            features["dpo"] = 365.0 if ap > 0 else 0.0
        else:
            features["dpo"] = safe_div(ap * 365.0, cogs, default=None, min_val=0.0, max_val=730.0)
    else:
        features["dpo"] = None

    # 3. DIO (Days Inventory Outstanding) = (Inventory * 365) / COGS
    if inv is not None and cogs is not None:
        if abs(cogs) < 1e-9:
            features["dio"] = 365.0 if inv > 0 else 0.0
        else:
            features["dio"] = safe_div(inv * 365.0, cogs, default=None, min_val=0.0, max_val=730.0)
    else:
        features["dio"] = None

    # 4. Cash Conversion Cycle (CCC) = DSO + DIO - DPO
    dso = features["dso"]
    dio = features["dio"]
    dpo = features["dpo"]
    if dso is not None and dio is not None and dpo is not None:
        features["cash_conversion_cycle"] = round(dso + dio - dpo, 2)
    else:
        features["cash_conversion_cycle"] = None

    # 5. Asset Turnover = Revenue / Total Assets
    features["asset_turnover"] = safe_div(rev, ta, default=None, min_val=0.0, max_val=20.0)

    return features


def compute_trend_and_growth(
    periods: List[FinancialStatementPeriod],
) -> Tuple[Dict[str, Optional[float]], Dict[str, bool]]:
    """Compute multi-period trend, volatility, and growth metrics.
    
    Expects periods sorted chronologically from oldest to newest (latest is periods[-1]).
    """
    features: Dict[str, Optional[float]] = {
        "yoy_sales_growth": None,
        "revenue_volatility": None,
        "margin_trend": None,
        "cash_flow_volatility": None,
    }
    flags: Dict[str, bool] = {
        "insufficient_periods_flag": False,
    }

    if len(periods) < 2:
        flags["insufficient_periods_flag"] = True
        return features, flags

    # Latest period and prior period
    latest = periods[-1]
    prior = periods[-2]

    # YoY Sales Growth
    if latest.total_revenue is not None and prior.total_revenue is not None:
        denom = abs(prior.total_revenue)
        if denom < 1e-9:
            features["yoy_sales_growth"] = 0.0
        else:
            growth = (latest.total_revenue - prior.total_revenue) / denom
            features["yoy_sales_growth"] = round(max(-1.0, min(5.0, growth)), 6)

    # Margin Trend (Operating Margin_t - Operating Margin_{t-1})
    lat_margin = safe_div(latest.operating_profit_ebit, latest.total_revenue)
    pri_margin = safe_div(prior.operating_profit_ebit, prior.total_revenue)
    if lat_margin is not None and pri_margin is not None:
        features["margin_trend"] = round(lat_margin - pri_margin, 6)

    # Multi-period volatilities
    revenues = [p.total_revenue for p in periods if p.total_revenue is not None]
    if len(revenues) >= 2:
        mean_rev = statistics.mean(revenues)
        if abs(mean_rev) > 1e-9:
            std_rev = statistics.stdev(revenues)
            features["revenue_volatility"] = round(std_rev / abs(mean_rev), 6)
        else:
            features["revenue_volatility"] = 0.0

    ocfs = [p.operating_cash_flow for p in periods if p.operating_cash_flow is not None]
    if len(ocfs) >= 2:
        mean_ocf = statistics.mean([abs(x) for x in ocfs])
        if abs(mean_ocf) > 1e-9:
            std_ocf = statistics.stdev(ocfs)
            features["cash_flow_volatility"] = round(std_ocf / mean_ocf, 6)
        else:
            features["cash_flow_volatility"] = 0.0

    return features, flags
