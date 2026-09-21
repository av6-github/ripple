"""Unit and integration tests for RIPPLE Feature Engine.

Verifies:
- FEAT-001: Current ratio normal, zero-denominator, and null handling
- FEAT-002: Quick ratio normal, zero inventory, and negative working capital
- FEAT-003: Debt/equity normal, negative equity distress, zero debt
- FEAT-004: Profitability margins and ROA/ROE under profit and loss
- FEAT-005: Interest coverage normal, zero interest expense, negative EBIT
- FEAT-006: Cash-flow volatility multi-period and single-period fallback
- FEAT-007: DSO, DPO, DIO, and Cash Conversion Cycle
- FEAT-008: Customer concentration (HHI)
- FEAT-009: Supplier concentration (HHI)
- LEAK-001: Target leakage rejection of post-prediction fields
- LEAK-003: Feature Dictionary schema alignment
"""

from datetime import date
import pytest
from backend.features.domain import (
    AlternativeDataInput,
    CounterpartyRelationship,
    FinancialStatementPeriod,
    InvoiceRecord,
    TargetLeakageError,
    TransactionRecord,
)
from backend.features.efficiency_trend import (
    compute_efficiency_ratios,
    compute_trend_and_growth,
)
from backend.features.feature_engine import FeatureEngine, LeakageGuard
from backend.features.financial_ratios import compute_financial_ratios, safe_div


# =====================================================================
# FEAT-001: Current Ratio
# =====================================================================

def test_feat_001_current_ratio_normal():
    period = FinancialStatementPeriod(
        current_assets=150_000.0,
        short_term_liabilities=100_000.0,
        total_assets=300_000.0,
        total_liabilities=150_000.0,
        total_equity=150_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["current_ratio"] == 1.5
    assert not flags["zero_short_term_debt_flag"]


def test_feat_001_current_ratio_zero_denominator():
    period = FinancialStatementPeriod(
        current_assets=150_000.0,
        short_term_liabilities=0.0,
        total_assets=300_000.0,
        total_liabilities=0.0,
        total_equity=300_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["current_ratio"] == 50.0  # Capped safe value
    assert flags["zero_short_term_debt_flag"] is True


def test_feat_001_current_ratio_null_inputs():
    period = FinancialStatementPeriod(
        current_assets=None,
        short_term_liabilities=100_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["current_ratio"] is None


# =====================================================================
# FEAT-002: Quick Ratio
# =====================================================================

def test_feat_002_quick_ratio_normal():
    period = FinancialStatementPeriod(
        current_assets=150_000.0,
        inventory=30_000.0,
        short_term_liabilities=100_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["quick_ratio"] == 1.2


def test_feat_002_quick_ratio_zero_inventory():
    period = FinancialStatementPeriod(
        current_assets=100_000.0,
        inventory=0.0,
        short_term_liabilities=100_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["quick_ratio"] == 1.0
    assert feats["current_ratio"] == 1.0


# =====================================================================
# FEAT-003: Debt to Equity & Negative Equity Handling
# =====================================================================

def test_feat_003_debt_to_equity_normal():
    period = FinancialStatementPeriod(
        total_liabilities=200_000.0,
        total_equity=100_000.0,
        total_assets=300_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["debt_to_equity"] == 2.0
    assert not flags["negative_equity_flag"]


def test_feat_003_debt_to_equity_negative_equity():
    """Negative equity must NOT produce a negative ratio that appears 'low risk'."""
    period = FinancialStatementPeriod(
        total_liabilities=250_000.0,
        total_equity=-50_000.0,  # Insolvent
        total_assets=200_000.0,
        net_profit=-20_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert flags["negative_equity_flag"] is True
    assert feats["debt_to_equity"] == 50.0  # Max distress cap
    assert feats["roe"] == -1.0  # Avoid (-)/(-) = (+) false profit artifact


def test_feat_003_debt_to_equity_zero_debt():
    period = FinancialStatementPeriod(
        total_liabilities=0.0,
        total_equity=100_000.0,
        total_assets=100_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["debt_to_equity"] == 0.0


# =====================================================================
# FEAT-004: Margins & Profitability
# =====================================================================

def test_feat_004_margins_and_profitability():
    period = FinancialStatementPeriod(
        total_revenue=500_000.0,
        gross_profit=150_000.0,
        operating_profit_ebit=75_000.0,
        net_profit=50_000.0,
        total_assets=250_000.0,
        total_equity=100_000.0,
    )
    feats, _ = compute_financial_ratios(period)
    assert feats["gross_margin"] == 0.30
    assert feats["operating_margin"] == 0.15
    assert feats["net_margin"] == 0.10
    assert feats["roa"] == 0.20
    assert feats["roe"] == 0.50


def test_feat_004_negative_profit_operating_loss():
    period = FinancialStatementPeriod(
        total_revenue=500_000.0,
        gross_profit=50_000.0,
        operating_profit_ebit=-25_000.0,
        net_profit=-35_000.0,
        total_assets=200_000.0,
        total_equity=50_000.0,
    )
    feats, _ = compute_financial_ratios(period)
    assert feats["operating_margin"] == -0.05
    assert feats["net_margin"] == -0.07
    assert feats["roa"] == -0.175
    assert feats["roe"] == -0.7


# =====================================================================
# FEAT-005: Interest Coverage
# =====================================================================

def test_feat_005_interest_coverage_normal():
    period = FinancialStatementPeriod(
        operating_profit_ebit=50_000.0,
        interest_expense=10_000.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["interest_coverage"] == 5.0
    assert not flags["zero_interest_expense_flag"]


def test_feat_005_interest_coverage_zero_interest():
    period = FinancialStatementPeriod(
        operating_profit_ebit=50_000.0,
        interest_expense=0.0,
    )
    feats, flags = compute_financial_ratios(period)
    assert feats["interest_coverage"] == 50.0  # Safe cap
    assert flags["zero_interest_expense_flag"] is True


def test_feat_005_interest_coverage_operating_loss():
    period = FinancialStatementPeriod(
        operating_profit_ebit=-20_000.0,
        interest_expense=10_000.0,
    )
    feats, _ = compute_financial_ratios(period)
    assert feats["interest_coverage"] == -2.0


# =====================================================================
# FEAT-006: Cash Flow Volatility & Multi-Period Trend
# =====================================================================

def test_feat_006_cash_flow_volatility_multi_period():
    p1 = FinancialStatementPeriod(fiscal_year=2021, total_revenue=100_000.0, operating_cash_flow=20_000.0)
    p2 = FinancialStatementPeriod(fiscal_year=2022, total_revenue=120_000.0, operating_cash_flow=25_000.0)
    p3 = FinancialStatementPeriod(fiscal_year=2023, total_revenue=150_000.0, operating_cash_flow=35_000.0)
    
    feats, flags = compute_trend_and_growth([p1, p2, p3])
    assert feats["cash_flow_volatility"] is not None
    assert feats["cash_flow_volatility"] > 0.0
    assert not flags["insufficient_periods_flag"]
    assert feats["yoy_sales_growth"] == 0.25  # (150k - 120k) / 120k


def test_feat_006_insufficient_periods_fallback():
    p1 = FinancialStatementPeriod(fiscal_year=2023, total_revenue=150_000.0, operating_cash_flow=35_000.0)
    feats, flags = compute_trend_and_growth([p1])
    assert feats["cash_flow_volatility"] is None
    assert feats["yoy_sales_growth"] is None
    assert flags["insufficient_periods_flag"] is True


# =====================================================================
# FEAT-007: Operating Efficiency (DSO, DPO, DIO, CCC)
# =====================================================================

def test_feat_007_efficiency_and_ccc():
    period = FinancialStatementPeriod(
        total_revenue=365_000.0,
        cost_of_goods_sold=200_000.0,
        accounts_receivable=45_000.0,
        accounts_payable=20_000.0,
        inventory=40_000.0,
        total_assets=300_000.0,
    )
    feats = compute_efficiency_ratios(period)
    # DSO = (45,000 * 365) / 365,000 = 45 days
    assert feats["dso"] == 45.0
    # DIO = (40,000 * 365) / 200,000 = 73 days
    assert feats["dio"] == 73.0
    # DPO = (20,000 * 365) / 200,000 = 36.5 days
    assert feats["dpo"] == 36.5
    # CCC = 45 + 73 - 36.5 = 81.5 days
    assert feats["cash_conversion_cycle"] == 81.5
    # Asset Turnover = 365,000 / 300,000 = 1.216667
    assert feats["asset_turnover"] == pytest.approx(1.216667, abs=1e-5)


# =====================================================================
# FEAT-008 & FEAT-009: Alternative Data (Concentration & Payments)
# =====================================================================

def test_feat_008_customer_concentration_monopoly():
    """A single customer represents 100% concentration (HHI = 1.0)."""
    alt = AlternativeDataInput(
        counterparties=[
            CounterpartyRelationship(
                counterparty_id="C1",
                counterparty_name="Sole Customer Corp",
                relationship_type="customer",
                annual_volume=1_000_000.0,
                tenure_months=24,
            )
        ]
    )
    engine = FeatureEngine()
    period = FinancialStatementPeriod(total_revenue=1_000_000.0)
    result = engine.extract_from_statements([period], alt_data=alt)
    assert result.features["customer_concentration"] == 1.0
    assert result.indicators["customer_concentration"]["status"] == "HIGH"


def test_feat_008_customer_concentration_diversified():
    """Four equal customers yields HHI = 4 * (0.25)^2 = 0.25."""
    alt = AlternativeDataInput(
        counterparties=[
            CounterpartyRelationship(counterparty_id=f"C{i}", counterparty_name=f"Client {i}", relationship_type="customer", annual_volume=250_000.0, tenure_months=12)
            for i in range(4)
        ]
    )
    engine = FeatureEngine()
    period = FinancialStatementPeriod(total_revenue=1_000_000.0)
    result = engine.extract_from_statements([period], alt_data=alt)
    assert result.features["customer_concentration"] == 0.25


def test_feat_009_supplier_concentration():
    """Two suppliers with 80% and 20% share yields HHI = 0.8^2 + 0.2^2 = 0.68."""
    alt = AlternativeDataInput(
        counterparties=[
            CounterpartyRelationship(counterparty_id="S1", counterparty_name="Primary Supplier", relationship_type="supplier", annual_volume=800_000.0, tenure_months=36),
            CounterpartyRelationship(counterparty_id="S2", counterparty_name="Secondary Supplier", relationship_type="supplier", annual_volume=200_000.0, tenure_months=12),
        ]
    )
    engine = FeatureEngine()
    period = FinancialStatementPeriod(total_revenue=1_500_000.0)
    result = engine.extract_from_statements([period], alt_data=alt)
    assert result.features["supplier_concentration"] == 0.68
    assert result.features["relationship_stability"] == 24.0  # avg of 36 and 12


def test_payment_timeliness_and_delays():
    invoices = [
        InvoiceRecord(invoice_id="INV-1", issue_date=date(2023, 1, 1), due_date=date(2023, 1, 31), payment_date=date(2023, 1, 28), amount=5000),  # on-time
        InvoiceRecord(invoice_id="INV-2", issue_date=date(2023, 2, 1), due_date=date(2023, 2, 28), payment_date=date(2023, 2, 25), amount=4000),  # on-time
        InvoiceRecord(invoice_id="INV-3", issue_date=date(2023, 3, 1), due_date=date(2023, 3, 31), payment_date=date(2023, 4, 15), amount=6000),  # late (15 days)
    ]
    alt = AlternativeDataInput(invoices=invoices)
    engine = FeatureEngine()
    period = FinancialStatementPeriod(total_revenue=50_000.0)
    res = engine.extract_from_statements([period], alt_data=alt)
    assert res.features["payment_timeliness"] == pytest.approx(0.6667, abs=1e-3)
    assert res.features["payment_consistency"] is not None


# =====================================================================
# LEAK-001: Target Leakage Rejection
# =====================================================================

def test_leak_001_target_leakage_rejection():
    """Any input with blacklisted outcome fields must raise TargetLeakageError."""
    engine = FeatureEngine()
    
    # Test 'class' key rejection
    with pytest.raises(TargetLeakageError, match="Target leakage detected"):
        engine.extract_from_raw_dict({
            "total_revenue": 100_000.0,
            "class": 1,
        })

    # Test 'charge_off_amount' rejection
    with pytest.raises(TargetLeakageError, match="Target leakage detected"):
        engine.extract_from_raw_dict({
            "total_revenue": 100_000.0,
            "charge_off_amount": 50_000.0,
        })

    # Test 'recovery_rate' rejection
    with pytest.raises(TargetLeakageError, match="Target leakage detected"):
        engine.extract_from_raw_dict({
            "total_revenue": 100_000.0,
            "recovery_rate": 0.25,
        })

    # Test 'post_decision_events' rejection
    with pytest.raises(TargetLeakageError, match="Target leakage detected"):
        engine.extract_from_raw_dict({
            "total_revenue": 100_000.0,
            "post_decision_events": "workout",
        })


# =====================================================================
# Polish Bankruptcy Vector Transformation
# =====================================================================

def test_polish_vector_transformation():
    engine = FeatureEngine()
    sample_polish_row = {
        "Attr1": "0.12",   # ROA
        "Attr2": "0.45",   # Debt ratio (TL / TA)
        "Attr3": "0.20",   # Working capital / TA
        "Attr4": "1.8",    # Current ratio
        "Attr10": "0.55",  # Equity / TA
        "Attr19": "0.25",  # Gross margin
        "Attr23": "0.08",  # Net margin
        "Attr27": "4.5",   # Interest coverage
        "Attr44": "42.0",  # DSO
        "Attr47": "35.0",  # DIO
        "Attr52": "30.0",  # DPO
        "Attr9": "1.5",    # Asset turnover
    }
    result = engine.extract_from_polish_vector(sample_polish_row)
    assert result.features["current_ratio"] == 1.8
    assert result.features["roa"] == 0.12
    assert result.features["debt_to_assets"] == 0.45
    assert result.features["debt_to_equity"] == pytest.approx(0.45 / 0.55, abs=1e-3)
    assert result.features["cash_conversion_cycle"] == 47.0  # 42 + 35 - 30


# =====================================================================
# LEAK-003: Feature Dictionary Alignment
# =====================================================================

def test_leak_003_feature_dictionary_alignment():
    """All features produced by FeatureEngine must be documented in docs/FEATURE_DICTIONARY.md."""
    engine = FeatureEngine()
    canonical_names = engine.get_feature_names()
    
    with open("/home/atharv-vedant/PROJECTS/ripple/docs/FEATURE_DICTIONARY.md", "r") as f:
        dict_content = f.read()
    
    for feat in canonical_names:
        assert f"`{feat}`" in dict_content, f"Feature '{feat}' is missing from docs/FEATURE_DICTIONARY.md"
