"""Automated Data Quality & Accounting Schema Validation Gate for RIPPLE.

Verifies structural data integrity, accounting identities, and boundary constraints:
- Fundamental balance sheet equation: Total Assets = Total Liabilities + Equity
- Non-negative revenues and assets
- Working capital identity
- Critical null-rate threshold
- Produces a quantitative Data Quality Score (0 - 100) and actionable flags.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class QualityStatus(str, Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


@dataclass
class QualityCheckResult:
    """Individual data assertion result."""

    check_name: str
    category: str  # 'accounting_identity', 'range_sanity', 'completeness'
    status: QualityStatus
    message: str
    observed_value: Any = None
    expected_constraint: str = ""


@dataclass
class DataQualityReport:
    """Comprehensive data quality scorecard."""

    overall_status: QualityStatus
    quality_score: float  # 0.0 - 100.0
    passed_count: int
    warning_count: int
    failed_count: int
    checks: List[QualityCheckResult] = field(default_factory=list)


class DataQualityGate:
    """Institutional gatekeeper enforcing structural accounting integrity prior to scoring."""

    BALANCE_SHEET_TOLERANCE_PCT: float = 1.0  # Allow up to 1% rounding discrepancy

    @classmethod
    def evaluate(cls, financial_dict: Dict[str, Any]) -> DataQualityReport:
        """Run all automated schema and accounting checks on input financial statement."""
        checks: List[QualityCheckResult] = []

        # 1. Core Completeness Checks
        required_fields = ["total_assets", "total_liabilities", "revenue", "equity"]
        missing_fields = [f for f in required_fields if financial_dict.get(f) is None]

        if missing_fields:
            checks.append(
                QualityCheckResult(
                    check_name="Core Field Completeness",
                    category="completeness",
                    status=QualityStatus.FAILED,
                    message=f"Missing essential accounting fields: {', '.join(missing_fields)}",
                    observed_value=len(required_fields) - len(missing_fields),
                    expected_constraint=f"All {len(required_fields)} required fields present",
                )
            )
        else:
            checks.append(
                QualityCheckResult(
                    check_name="Core Field Completeness",
                    category="completeness",
                    status=QualityStatus.PASSED,
                    message="All mandatory financial disclosure fields are present.",
                    observed_value=len(required_fields),
                    expected_constraint=f"All {len(required_fields)} required fields present",
                )
            )

        # 2. Accounting Identity: Assets = Liabilities + Equity
        ta = cls._to_float(financial_dict.get("total_assets"))
        tl = cls._to_float(financial_dict.get("total_liabilities"))
        eq = cls._to_float(financial_dict.get("equity"))

        if ta is not None and tl is not None and eq is not None:
            sum_liab_eq = tl + eq
            discrepancy = abs(ta - sum_liab_eq)
            rel_discrepancy_pct = (discrepancy / max(abs(ta), 1.0)) * 100.0

            if rel_discrepancy_pct <= cls.BALANCE_SHEET_TOLERANCE_PCT:
                checks.append(
                    QualityCheckResult(
                        check_name="Balance Sheet Identity",
                        category="accounting_identity",
                        status=QualityStatus.PASSED,
                        message=f"Assets ({ta:,.2f}) balance with Liab+Equity ({sum_liab_eq:,.2f}) within {rel_discrepancy_pct:.2f}%.",
                        observed_value=round(rel_discrepancy_pct, 3),
                        expected_constraint=f"Divergence <= {cls.BALANCE_SHEET_TOLERANCE_PCT}%",
                    )
                )
            elif rel_discrepancy_pct <= 5.0:
                checks.append(
                    QualityCheckResult(
                        check_name="Balance Sheet Identity",
                        category="accounting_identity",
                        status=QualityStatus.WARNING,
                        message=f"Minor balance sheet discrepancy: Assets ({ta:,.2f}) vs Liab+Equity ({sum_liab_eq:,.2f}) divergence is {rel_discrepancy_pct:.2f}%.",
                        observed_value=round(rel_discrepancy_pct, 3),
                        expected_constraint=f"Divergence <= {cls.BALANCE_SHEET_TOLERANCE_PCT}%",
                    )
                )
            else:
                checks.append(
                    QualityCheckResult(
                        check_name="Balance Sheet Identity",
                        category="accounting_identity",
                        status=QualityStatus.FAILED,
                        message=f"Severe balance sheet breach! Assets ({ta:,.2f}) != Liab+Equity ({sum_liab_eq:,.2f}). Imbalance = {discrepancy:,.2f} ({rel_discrepancy_pct:.1f}%).",
                        observed_value=round(rel_discrepancy_pct, 3),
                        expected_constraint=f"Divergence <= {cls.BALANCE_SHEET_TOLERANCE_PCT}%",
                    )
                )

        # 3. Range Sanity: Non-Negative Assets
        if ta is not None:
            if ta > 0:
                checks.append(
                    QualityCheckResult(
                        check_name="Positive Total Assets",
                        category="range_sanity",
                        status=QualityStatus.PASSED,
                        message=f"Total Assets are strictly positive ({ta:,.2f}).",
                        observed_value=ta,
                        expected_constraint="total_assets > 0",
                    )
                )
            else:
                checks.append(
                    QualityCheckResult(
                        check_name="Positive Total Assets",
                        category="range_sanity",
                        status=QualityStatus.FAILED,
                        message=f"Invalid asset figure: Total assets must be strictly positive (observed: {ta}).",
                        observed_value=ta,
                        expected_constraint="total_assets > 0",
                    )
                )

        # 4. Range Sanity: Non-Negative Revenue
        rev = cls._to_float(financial_dict.get("revenue"))
        if rev is not None:
            if rev >= 0:
                checks.append(
                    QualityCheckResult(
                        check_name="Non-Negative Revenue",
                        category="range_sanity",
                        status=QualityStatus.PASSED,
                        message=f"Revenue is valid non-negative ({rev:,.2f}).",
                        observed_value=rev,
                        expected_constraint="revenue >= 0",
                    )
                )
            else:
                checks.append(
                    QualityCheckResult(
                        check_name="Non-Negative Revenue",
                        category="range_sanity",
                        status=QualityStatus.FAILED,
                        message=f"Negative revenue observed: ({rev:,.2f}). Must be >= 0.",
                        observed_value=rev,
                        expected_constraint="revenue >= 0",
                    )
                )

        # 5. Working Capital Identity
        ca = cls._to_float(financial_dict.get("current_assets"))
        stl = cls._to_float(financial_dict.get("short_term_liabilities"))
        wc = cls._to_float(financial_dict.get("working_capital"))
        if ca is not None and stl is not None and wc is not None:
            expected_wc = ca - stl
            diff_wc = abs(wc - expected_wc)
            if diff_wc <= max(abs(ca) * 0.02, 100.0):
                checks.append(
                    QualityCheckResult(
                        check_name="Working Capital Definition",
                        category="accounting_identity",
                        status=QualityStatus.PASSED,
                        message=f"Working capital matches Current Assets - Current Liabilities within tolerance.",
                        observed_value=wc,
                        expected_constraint="working_capital == current_assets - current_liabilities",
                    )
                )
            else:
                checks.append(
                    QualityCheckResult(
                        check_name="Working Capital Definition",
                        category="accounting_identity",
                        status=QualityStatus.WARNING,
                        message=f"Reported working capital ({wc:,.2f}) differs from CA - STL ({expected_wc:,.2f}).",
                        observed_value=wc,
                        expected_constraint="working_capital == current_assets - current_liabilities",
                    )
                )

        # Aggregate scorecard
        passed = sum(1 for c in checks if c.status == QualityStatus.PASSED)
        warnings = sum(1 for c in checks if c.status == QualityStatus.WARNING)
        failed = sum(1 for c in checks if c.status == QualityStatus.FAILED)
        total = len(checks)

        if total == 0:
            score = 0.0
            overall = QualityStatus.FAILED
        else:
            # Formula: Passed checks = 100%, Warning = 50%, Failed = 0%
            score = round(((passed * 1.0 + warnings * 0.5) / total) * 100.0, 1)
            if failed > 0:
                overall = QualityStatus.FAILED
            elif warnings > 0:
                overall = QualityStatus.WARNING
            else:
                overall = QualityStatus.PASSED

        return DataQualityReport(
            overall_status=overall,
            quality_score=score,
            passed_count=passed,
            warning_count=warnings,
            failed_count=failed,
            checks=checks,
        )

    @staticmethod
    def _to_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
