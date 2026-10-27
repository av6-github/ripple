"""The single authoritative Feature Engine for RIPPLE.

Shared by training pipelines and live ML inference in accordance with:
- ARCHITECTURE.md Section 6 (Single Authoritative Engine)
- AGENTS.md Rule 4.5 & LEAKAGE_AUDIT.md (LeakageGuard)
- AGENTS.md Rule 15 & FEATURE_DICTIONARY.md (Feature Dictionary compliance)
"""

from typing import Any, Dict, List, Optional, Set
from backend.features.alternative_data import compute_alternative_features
from backend.features.domain import (
    AlternativeDataInput,
    FeatureEngineResult,
    FinancialStatementPeriod,
    TargetLeakageError,
)
from backend.features.efficiency_trend import (
    compute_efficiency_ratios,
    compute_trend_and_growth,
)
from backend.features.financial_ratios import compute_financial_ratios


class LeakageGuard:
    """Strict guard preventing post-decision information and outcome targets from entering features."""

    FORBIDDEN_EXACT_KEYS: Set[str] = {
        "class",
        "target",
        "default_class",
        "is_bankrupt",
        "bankrupt",
        "charge_off",
        "charge_off_amount",
        "charge_off_date",
        "recovery",
        "recovery_rate",
        "recovery_amount",
        "post_decision_events",
        "subsequent_delinquency",
        "forbearance_flag",
        "actual_loss",
        "loss_given_default",
    }

    FORBIDDEN_SUBSTRINGS: List[str] = [
        "charge_off",
        "recovery",
        "post_decision",
    ]

    @classmethod
    def check_keys(cls, keys: List[str]) -> None:
        """Verify that no forbidden target or post-decision key is present."""
        for k in keys:
            norm_k = k.lower().strip()
            if norm_k in cls.FORBIDDEN_EXACT_KEYS:
                raise TargetLeakageError(
                    f"Target leakage detected! Key '{k}' is forbidden in feature inputs."
                )
            for sub in cls.FORBIDDEN_SUBSTRINGS:
                if sub in norm_k:
                    raise TargetLeakageError(
                        f"Target leakage detected! Substring '{sub}' found in key '{k}'."
                    )


class FeatureEngine:
    """Central engine computing standardized financial ratios, efficiency, trend, and alternative features."""

    CANONICAL_FEATURES: List[str] = [
        # Liquidity
        "current_ratio",
        "quick_ratio",
        "cash_ratio",
        "working_capital_to_assets",
        "working_capital_to_revenue",
        # Leverage
        "debt_to_equity",
        "debt_to_assets",
        "net_debt_to_ebitda",
        "equity_ratio",
        # Profitability
        "gross_margin",
        "operating_margin",
        "net_margin",
        "roa",
        "roe",
        # Coverage
        "interest_coverage",
        "dscr",
        # Cash Flow
        "ocf_to_revenue",
        "ocf_to_total_debt",
        "accrual_quality",
        "cash_flow_volatility",
        # Efficiency
        "dso",
        "dpo",
        "dio",
        "cash_conversion_cycle",
        "asset_turnover",
        "working_capital_fragility_velocity",
        # Trend / Growth
        "yoy_sales_growth",
        "revenue_volatility",
        "margin_trend",
        # Alternative Data
        "transaction_frequency",
        "transaction_volume",
        "transaction_size_variability",
        "payment_timeliness",
        "payment_delay_trend",
        "payment_consistency",
        "customer_concentration",
        "supplier_concentration",
        "relationship_stability",
    ]

    def __init__(self) -> None:
        self.guard = LeakageGuard()

    def get_feature_names(self) -> List[str]:
        """Return the canonical list of computed feature names."""
        return list(self.CANONICAL_FEATURES)

    def extract_from_statements(
        self,
        periods: List[FinancialStatementPeriod],
        alt_data: Optional[AlternativeDataInput] = None,
    ) -> FeatureEngineResult:
        """Compute full feature set from ordered financial periods and alternative data."""
        if not periods:
            raise ValueError("At least one financial period is required.")

        # Check leakage on raw inputs
        for p in periods:
            self.guard.check_keys(list(p.model_dump().keys()))

        # Latest period is used for point-in-time ratios
        latest_period = periods[-1]

        # 1. Financial Ratios
        fin_feats, fin_flags = compute_financial_ratios(latest_period)

        # 2. Efficiency Ratios
        eff_feats = compute_efficiency_ratios(latest_period)

        # 3. Trend & Growth Metrics
        trend_feats, trend_flags = compute_trend_and_growth(periods)

        # 4. Alternative Data Features
        alt_feats, alt_flags = compute_alternative_features(alt_data)

        # 5. Polish Dataset Model Attributes (Attr1..Attr64) for Tabular ML Engine
        polish_attrs = self.compute_polish_attributes(latest_period)

        # Combine all features
        all_features: Dict[str, Optional[float]] = {}
        for k in self.CANONICAL_FEATURES:
            if k in fin_feats:
                all_features[k] = fin_feats[k]
            elif k in eff_feats:
                all_features[k] = eff_feats[k]
            elif k in trend_feats:
                all_features[k] = trend_feats[k]
            elif k in alt_feats:
                all_features[k] = alt_feats[k]
            else:
                all_features[k] = None

        # Include mapped Polish attributes so ML model receives authentic borrower ratios
        all_features.update(polish_attrs)

        # Combine flags
        all_flags: Dict[str, bool] = {}
        all_flags.update(fin_flags)
        all_flags.update(trend_flags)
        all_flags.update(alt_flags)

        # Completeness calculation
        non_null = sum(1 for v in all_features.values() if v is not None)
        completeness = round(non_null / len(self.CANONICAL_FEATURES), 4)

        # Generate human indicators
        indicators = self._build_human_indicators(all_features, all_flags)

        return FeatureEngineResult(
            features=all_features,
            flags=all_flags,
            indicators=indicators,
            feature_completeness=completeness,
        )

    def extract_from_raw_dict(
        self,
        data: Dict[str, Any],
        alt_data: Optional[AlternativeDataInput] = None,
    ) -> FeatureEngineResult:
        """Extract features from a dictionary representation of financial inputs."""
        self.guard.check_keys(list(data.keys()))
        period = FinancialStatementPeriod(**data)
        return self.extract_from_statements([period], alt_data=alt_data)

    def extract_from_polish_vector(
        self,
        row: Dict[str, Any],
        alt_data: Optional[AlternativeDataInput] = None,
    ) -> FeatureEngineResult:
        """Transform a Polish bankruptcy row (Attr1..Attr64) into the unified feature dictionary."""
        # Guard against target leakage
        self.guard.check_keys(list(row.keys()))

        def get_val(name: str) -> Optional[float]:
            v = row.get(name) or row.get(name.lower()) or row.get(name.upper())
            if v is None or v == "" or v == "?":
                return None
            try:
                val = float(v)
                return None if val != val else val  # check NaN
            except (ValueError, TypeError):
                return None

        features: Dict[str, Optional[float]] = {}
        flags: Dict[str, bool] = {
            "negative_equity_flag": False,
            "negative_ebitda_flag": False,
            "zero_interest_expense_flag": False,
            "zero_short_term_debt_flag": False,
            "zero_revenue_flag": False,
            "insufficient_periods_flag": True,  # Polish single-year snapshot has no multi-period series
        }

        # Liquidity
        features["current_ratio"] = get_val("Attr4")
        features["quick_ratio"] = get_val("Attr46")
        features["cash_ratio"] = get_val("Attr40")
        features["working_capital_to_assets"] = get_val("Attr3")
        features["working_capital_to_revenue"] = None  # derived in multi-statement

        # Leverage
        x2 = get_val("Attr2")  # total liabilities / total assets
        x10 = get_val("Attr10")  # equity / total assets
        if x10 is not None and x10 <= 0:
            flags["negative_equity_flag"] = True
            features["debt_to_equity"] = 50.0
            features["roe"] = -1.0
        elif x2 is not None and x10 is not None and x10 > 0:
            features["debt_to_equity"] = round(x2 / x10, 4)
            features["roe"] = get_val("Attr13")
        else:
            features["debt_to_equity"] = None
            features["roe"] = get_val("Attr13")

        features["debt_to_assets"] = x2
        features["net_debt_to_ebitda"] = None
        features["equity_ratio"] = x10

        # Profitability
        features["gross_margin"] = get_val("Attr19")
        features["operating_margin"] = get_val("Attr39") or get_val("Attr42")
        features["net_margin"] = get_val("Attr23")
        features["roa"] = get_val("Attr1")

        # Coverage
        features["interest_coverage"] = get_val("Attr27")
        features["dscr"] = None

        # Cash Flow
        features["ocf_to_revenue"] = None
        features["ocf_to_total_debt"] = None
        features["accrual_quality"] = None
        features["cash_flow_volatility"] = None

        # Efficiency
        features["dso"] = get_val("Attr44")
        features["dpo"] = get_val("Attr52")
        features["dio"] = get_val("Attr47")
        if features["dso"] is not None and features["dio"] is not None and features["dpo"] is not None:
            features["cash_conversion_cycle"] = round(
                features["dso"] + features["dio"] - features["dpo"], 2
            )
        else:
            features["cash_conversion_cycle"] = None
        features["asset_turnover"] = get_val("Attr9")

        # Working Capital Fragility Velocity
        x51 = get_val("Attr51")
        x10 = get_val("Attr10")
        dso_val = features["dso"]
        dpo_val = features["dpo"]
        ccc_val = features["cash_conversion_cycle"]
        if dso_val is not None and dpo_val is not None and ccc_val is not None:
            gap = dso_val - dpo_val
            norm_ccc = max(abs(ccc_val), 1.0)
            gap_int = gap / norm_ccc
            if x51 is not None and x10 is not None:
                if x10 <= 0:
                    lev = 10.0 if x51 > 0 else 1.0
                else:
                    lev = max(0.0, min(20.0, x51 / x10))
                features["working_capital_fragility_velocity"] = round(float(gap_int * lev), 4)
            else:
                features["working_capital_fragility_velocity"] = round(float(gap_int), 4)
        else:
            features["working_capital_fragility_velocity"] = None

        # Growth / Trend
        features["yoy_sales_growth"] = get_val("Attr21")
        features["revenue_volatility"] = None
        features["margin_trend"] = None

        # Alternative features
        alt_feats, alt_flags = compute_alternative_features(alt_data)
        features.update(alt_feats)
        flags.update(alt_flags)

        # Standardize order
        ordered_features = {k: features.get(k) for k in self.CANONICAL_FEATURES}

        non_null = sum(1 for v in ordered_features.values() if v is not None)
        completeness = round(non_null / len(self.CANONICAL_FEATURES), 4)
        indicators = self._build_human_indicators(ordered_features, flags)

        return FeatureEngineResult(
            features=ordered_features,
            flags=flags,
            indicators=indicators,
            feature_completeness=completeness,
        )

    @staticmethod
    def compute_polish_attributes(period: FinancialStatementPeriod) -> Dict[str, float]:
        """Compute Polish dataset attribute ratios (Attr1..Attr64) from financial line items."""
        import numpy as np

        ta = float(period.total_assets) if period.total_assets else 0.0
        ca = float(period.current_assets) if period.current_assets else 0.0
        cash = float(period.cash_and_equivalents) if period.cash_and_equivalents else 0.0
        inv = float(period.inventory) if period.inventory else 0.0
        tl = float(period.total_liabilities) if period.total_liabilities else 0.0
        stl = float(period.short_term_liabilities) if period.short_term_liabilities else 0.0
        eq = float(period.total_equity) if period.total_equity else 0.0
        rev = float(period.total_revenue) if period.total_revenue else 0.0
        cogs = float(period.cost_of_goods_sold) if period.cost_of_goods_sold else 0.0
        gp = float(period.gross_profit) if period.gross_profit else 0.0
        ebit = float(period.operating_profit_ebit) if period.operating_profit_ebit else 0.0
        np_val = float(period.net_profit) if period.net_profit else 0.0
        ocf = float(period.operating_cash_flow) if period.operating_cash_flow else 0.0
        ie = float(period.interest_expense) if period.interest_expense else 1.0
        ar = float(period.accounts_receivable) if period.accounts_receivable else 0.0

        attrs: Dict[str, float] = {}
        if ta > 0:
            attrs["Attr1"] = np_val / ta
            attrs["Attr2"] = tl / ta
            attrs["Attr3"] = (ca - stl) / ta
            attrs["Attr6"] = (eq - min(50000.0, eq * 0.2)) / ta
            attrs["Attr7"] = ebit / ta
            attrs["Attr9"] = rev / ta
            attrs["Attr10"] = eq / ta
            attrs["Attr11"] = gp / ta
            attrs["Attr14"] = (gp + ie) / ta
            attrs["Attr18"] = gp / ta
            attrs["Attr22"] = ebit / ta
            attrs["Attr24"] = gp / ta
            attrs["Attr25"] = eq / ta
            attrs["Attr29"] = float(np.log(max(ta, 1.0)))
            attrs["Attr36"] = rev / ta
            attrs["Attr38"] = eq / ta
            attrs["Attr48"] = (ebit + ocf) / ta
            attrs["Attr51"] = stl / ta

        if stl > 0:
            attrs["Attr4"] = ca / stl
            attrs["Attr12"] = gp / stl
            attrs["Attr40"] = cash / stl
            attrs["Attr46"] = (ca - inv) / stl
            attrs["Attr63"] = rev / stl

        if tl > 0:
            attrs["Attr8"] = eq / tl
            attrs["Attr16"] = ocf / tl
            attrs["Attr17"] = ta / tl
            attrs["Attr26"] = (np_val + ocf) / tl
            attrs["Attr50"] = ca / tl

        if eq != 0:
            attrs["Attr13"] = np_val / eq

        if rev > 0:
            attrs["Attr19"] = gp / rev
            attrs["Attr23"] = np_val / rev
            attrs["Attr30"] = (tl - cash) / rev
            attrs["Attr39"] = ebit / rev
            attrs["Attr42"] = ebit / rev
            attrs["Attr44"] = (ar / rev) * 365
            attrs["Attr56"] = gp / rev
            attrs["Attr58"] = (rev - np_val) / rev

        if cogs > 0:
            attrs["Attr47"] = (inv / cogs) * 365
            attrs["Attr52"] = (stl / cogs) * 365

        attrs["Attr55"] = ca - stl
        if (ta - ca) > 0:
            attrs["Attr64"] = rev / (ta - ca)

        attrs["Attr21"] = 1.05

        return attrs

    def _build_human_indicators(
        self,
        features: Dict[str, Optional[float]],
        flags: Dict[str, bool],
    ) -> Dict[str, Dict[str, Any]]:
        """Generate human-readable indicator assessments for bank officers and SMEs."""
        indicators: Dict[str, Dict[str, Any]] = {}

        # Current ratio
        cr = features.get("current_ratio")
        if cr is not None:
            if cr >= 1.5:
                status, desc = "HEALTHY", "Comfortable short-term liquidity cushion."
            elif cr >= 1.0:
                status, desc = "ADEQUATE", "Adequate liquidity; monitoring recommended."
            else:
                status, desc = "CRITICAL", "Short-term liabilities exceed current assets."
            indicators["current_ratio"] = {"value": cr, "status": status, "interpretation": desc}

        # Debt to Equity
        dte = features.get("debt_to_equity")
        if flags.get("negative_equity_flag"):
            indicators["debt_to_equity"] = {
                "value": dte,
                "status": "CRITICAL",
                "interpretation": "Negative equity indicates balance-sheet insolvency.",
            }
        elif dte is not None:
            if dte <= 1.5:
                status, desc = "HEALTHY", "Prudent leverage with strong equity cushion."
            elif dte <= 3.0:
                status, desc = "MODERATE", "Moderate debt burden."
            else:
                status, desc = "ELEVATED", "High leverage relative to equity base."
            indicators["debt_to_equity"] = {"value": dte, "status": status, "interpretation": desc}

        # Operating Margin
        om = features.get("operating_margin")
        if om is not None:
            if om >= 0.15:
                status, desc = "STRONG", "Strong core operating profitability."
            elif om >= 0.05:
                status, desc = "MODERATE", "Acceptable operating margins."
            elif om >= 0.0:
                status, desc = "THIN", "Thin operating profit margin."
            else:
                status, desc = "LOSS", "Operating at a commercial loss."
            indicators["operating_margin"] = {"value": om, "status": status, "interpretation": desc}

        # Payment timeliness
        pt = features.get("payment_timeliness")
        if pt is not None:
            if pt >= 0.90:
                status, desc = "EXCELLENT", "Consistently pays suppliers and invoices on time."
            elif pt >= 0.75:
                status, desc = "FAIR", "Occasional delayed payments."
            else:
                status, desc = "POOR", "Frequent late payments indicating cash flow strain."
            indicators["payment_timeliness"] = {"value": pt, "status": status, "interpretation": desc}

        # Customer Concentration
        cc = features.get("customer_concentration")
        if cc is not None:
            if cc <= 0.15:
                status, desc = "DIVERSIFIED", "Healthy, well-diversified customer base."
            elif cc <= 0.25:
                status, desc = "MODERATE", "Moderate customer concentration."
            else:
                status, desc = "HIGH", "High dependency on top customer accounts."
            indicators["customer_concentration"] = {"value": cc, "status": status, "interpretation": desc}

        # Working Capital Fragility Velocity
        wcfv = features.get("working_capital_fragility_velocity")
        if wcfv is not None:
            if wcfv <= 0.0:
                status, desc = "OPTIMAL", "Receivables collected faster than payables; negative working capital funding burden."
            elif wcfv <= 0.75:
                status, desc = "MANAGEABLE", "Mild working capital mismatch comfortably buffered by equity."
            elif wcfv <= 2.0:
                status, desc = "ELEVATED", "Trade credit gap is expanding and funded primarily by short-term obligations."
            else:
                status, desc = "ACUTE_FRAGILITY", "Severe liquidity drain velocity; high risk of cash crunch under supply shock."
            indicators["working_capital_fragility_velocity"] = {"value": wcfv, "status": status, "interpretation": desc}

        return indicators
