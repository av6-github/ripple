"""Authoritative Financial Ratio calculations for RIPPLE.

Implements SRS FR-04, handling edge cases:
- Division by zero
- Negative equity
- Zero interest expense
- Capping extreme infinities
"""

import math
from typing import Dict, Optional, Tuple
from backend.features.domain import FinancialStatementPeriod


def safe_div(
    numerator: Optional[float],
    denominator: Optional[float],
    default: Optional[float] = None,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> Optional[float]:
    """Safely divide two numbers, protecting against None, zero, and infinite values."""
    if numerator is None or denominator is None:
        return default
    if math.isnan(numerator) or math.isnan(denominator):
        return default
    if abs(denominator) < 1e-9:
        return default

    val = numerator / denominator
    if math.isinf(val) or math.isnan(val):
        return default

    if min_val is not None:
        val = max(min_val, val)
    if max_val is not None:
        val = min(max_val, val)
    return round(val, 6)


def compute_financial_ratios(
    period: FinancialStatementPeriod,
) -> Tuple[Dict[str, Optional[float]], Dict[str, bool]]:
    """Compute financial ratios and data-quality/distress flags for a single period."""
    features: Dict[str, Optional[float]] = {}
    flags: Dict[str, bool] = {
        "negative_equity_flag": False,
        "negative_ebitda_flag": False,
        "zero_interest_expense_flag": False,
        "zero_short_term_debt_flag": False,
        "zero_revenue_flag": False,
    }

    # Extract raw values
    ca = period.current_assets
    stl = period.short_term_liabilities
    cash = period.cash_and_equivalents
    inv = period.inventory if period.inventory is not None else 0.0
    ta = period.total_assets
    tl = period.total_liabilities
    eq = period.total_equity
    rev = period.total_revenue
    gp = period.gross_profit
    ebit = period.operating_profit_ebit
    ebitda = period.ebitda if period.ebitda is not None else ebit
    interest = period.interest_expense if period.interest_expense is not None else 0.0
    np_val = period.net_profit
    ocf = period.operating_cash_flow

    # 1. Liquidity Ratios
    if stl is not None and abs(stl) < 1e-9:
        flags["zero_short_term_debt_flag"] = True
        features["current_ratio"] = 50.0 if ca is not None and ca > 0 else 0.0
        features["quick_ratio"] = 50.0 if ca is not None and (ca - inv) > 0 else 0.0
        features["cash_ratio"] = 50.0 if cash is not None and cash > 0 else 0.0
    else:
        features["current_ratio"] = safe_div(ca, stl, default=None, min_val=0.0, max_val=50.0)
        features["quick_ratio"] = (
            safe_div(ca - inv, stl, default=None, min_val=0.0, max_val=50.0)
            if ca is not None and stl is not None
            else None
        )
        features["cash_ratio"] = safe_div(cash, stl, default=None, min_val=0.0, max_val=50.0)

    if ca is not None and stl is not None:
        wc = ca - stl
        features["working_capital_to_assets"] = safe_div(wc, ta, default=None, min_val=-2.0, max_val=2.0)
        if rev is not None and abs(rev) < 1e-9:
            flags["zero_revenue_flag"] = True
            features["working_capital_to_revenue"] = 0.0
        else:
            features["working_capital_to_revenue"] = safe_div(wc, rev, default=None, min_val=-5.0, max_val=5.0)
    else:
        features["working_capital_to_assets"] = None
        features["working_capital_to_revenue"] = None

    # 2. Leverage & Solvency Ratios
    if eq is not None and eq <= 0:
        flags["negative_equity_flag"] = True
        # In credit risk, negative equity is extreme distress; do NOT divide tl / (-eq) which makes a negative ratio
        features["debt_to_equity"] = 50.0  # Max distress cap
        features["roe"] = -1.0  # Loss or distress cap, avoiding (-profit)/(-equity) artifact
    else:
        features["debt_to_equity"] = safe_div(tl, eq, default=None, min_val=0.0, max_val=50.0)
        features["roe"] = safe_div(np_val, eq, default=None, min_val=-2.0, max_val=2.0)

    features["debt_to_assets"] = safe_div(tl, ta, default=None, min_val=0.0, max_val=10.0)
    features["equity_ratio"] = safe_div(eq, ta, default=None, min_val=-2.0, max_val=1.0)

    # Net Debt / EBITDA
    if tl is not None and cash is not None:
        net_debt = tl - cash
        if ebitda is not None and ebitda <= 0:
            flags["negative_ebitda_flag"] = True
            features["net_debt_to_ebitda"] = 20.0 if net_debt > 0 else 0.0
        else:
            features["net_debt_to_ebitda"] = safe_div(net_debt, ebitda, default=None, min_val=-5.0, max_val=20.0)
    else:
        features["net_debt_to_ebitda"] = None

    # 3. Profitability Ratios
    if rev is not None and abs(rev) < 1e-9:
        flags["zero_revenue_flag"] = True
        features["gross_margin"] = 0.0
        features["operating_margin"] = 0.0
        features["net_margin"] = 0.0
    else:
        features["gross_margin"] = safe_div(gp, rev, default=None, min_val=-1.0, max_val=1.0)
        features["operating_margin"] = safe_div(ebit, rev, default=None, min_val=-2.0, max_val=1.0)
        features["net_margin"] = safe_div(np_val, rev, default=None, min_val=-2.0, max_val=1.0)

    features["roa"] = safe_div(np_val, ta, default=None, min_val=-2.0, max_val=2.0)

    # 4. Coverage Ratios
    if interest is not None and abs(interest) < 1e-9:
        flags["zero_interest_expense_flag"] = True
        features["interest_coverage"] = 50.0 if ebit is not None and ebit > 0 else 0.0
    else:
        features["interest_coverage"] = safe_div(ebit, interest, default=None, min_val=-20.0, max_val=50.0)

    # DSCR = OCF / (short_term_liabilities + interest_expense)
    if ocf is not None and stl is not None:
        debt_service = stl + (interest if interest is not None else 0.0)
        if abs(debt_service) < 1e-9:
            features["dscr"] = 50.0 if ocf > 0 else 0.0
        else:
            features["dscr"] = safe_div(ocf, debt_service, default=None, min_val=-5.0, max_val=50.0)
    else:
        features["dscr"] = None

    # 5. Cash Flow Dynamics
    features["ocf_to_revenue"] = safe_div(ocf, rev, default=None, min_val=-2.0, max_val=2.0)
    features["ocf_to_total_debt"] = safe_div(ocf, tl, default=None, min_val=-2.0, max_val=2.0)

    if np_val is not None and ocf is not None and ta is not None:
        accruals = np_val - ocf
        features["accrual_quality"] = safe_div(accruals, ta, default=None, min_val=-1.0, max_val=1.0)
    else:
        features["accrual_quality"] = None

    return features, flags
