"""
Financial Data Validation Engine (SRS FR-03)
Detects accounting inconsistencies, invalid ranges, and negative revenue anomalies.
"""

from typing import List, Optional
from datetime import date

from backend.domain.schemas import FinancialStatementData, DataQualityViolation
from backend.domain.enums import QualityFlagType, Severity


class ValidationEngine:
    """Validates financial statement data and produces structured quality flags."""

    @staticmethod
    def validate(data: FinancialStatementData) -> List[DataQualityViolation]:
        violations: List[DataQualityViolation] = []

        # 1. VAL-001: Negative Revenue Check
        if data.revenue is not None and data.revenue < 0:
            violations.append(DataQualityViolation(
                field_name="revenue",
                flag_type=QualityFlagType.INVALID_RANGE,
                severity=Severity.CRITICAL,
                message="Revenue cannot be negative.",
                actual_value=str(data.revenue),
                expected_condition="revenue >= 0"
            ))

        # 2. VAL-002: Accounting Identity Check: Assets = Liabilities + Equity
        # Allow tolerance of $1.00 or 1.0% due to rounding
        if (
            data.total_assets is not None and 
            data.total_liabilities is not None and 
            data.equity is not None
        ):
            sum_liab_eq = data.total_liabilities + data.equity
            diff = abs(data.total_assets - sum_liab_eq)
            # 1% tolerance
            threshold = max(1.0, 0.01 * max(abs(data.total_assets), abs(sum_liab_eq)))
            if diff > threshold:
                violations.append(DataQualityViolation(
                    field_name="total_assets",
                    flag_type=QualityFlagType.ACCOUNTING_INCONSISTENCY,
                    severity=Severity.CRITICAL,
                    message=f"Balance sheet mismatch: Total Assets ({data.total_assets:,.2f}) != Liabilities ({data.total_liabilities:,.2f}) + Equity ({data.equity:,.2f}). Imbalance: {diff:,.2f}",
                    actual_value=f"Assets: {data.total_assets}, Liab+Eq: {sum_liab_eq}",
                    expected_condition="Total Assets == Total Liabilities + Equity"
                ))

        # 3. VAL-003: Future Date Check
        if data.period_end_date is not None and data.period_end_date > date.today():
            violations.append(DataQualityViolation(
                field_name="period_end_date",
                flag_type=QualityFlagType.FUTURE_DATE,
                severity=Severity.CRITICAL,
                message=f"Financial statement period end date {data.period_end_date} is in the future.",
                actual_value=str(data.period_end_date),
                expected_condition="period_end_date <= current_date"
            ))

        # 4. Range Validations
        if data.total_assets is not None and data.total_assets < 0:
            violations.append(DataQualityViolation(
                field_name="total_assets",
                flag_type=QualityFlagType.INVALID_RANGE,
                severity=Severity.CRITICAL,
                message="Total assets cannot be strictly negative.",
                actual_value=str(data.total_assets),
                expected_condition="total_assets >= 0"
            ))

        if data.cash_and_equivalents is not None and data.cash_and_equivalents < 0:
            violations.append(DataQualityViolation(
                field_name="cash_and_equivalents",
                flag_type=QualityFlagType.INVALID_RANGE,
                severity=Severity.WARNING,
                message="Cash balance is reported as negative (bank overdraft indicated).",
                actual_value=str(data.cash_and_equivalents),
                expected_condition="cash_and_equivalents >= 0"
            ))

        # 5. Working Capital Check: Current Assets - Current Liabilities
        if (
            data.current_assets is not None and 
            data.short_term_liabilities is not None and 
            data.working_capital is not None
        ):
            calc_wc = data.current_assets - data.short_term_liabilities
            if abs(calc_wc - data.working_capital) > max(1.0, 0.02 * abs(calc_wc)):
                violations.append(DataQualityViolation(
                    field_name="working_capital",
                    flag_type=QualityFlagType.ACCOUNTING_INCONSISTENCY,
                    severity=Severity.WARNING,
                    message=f"Working capital inconsistency: Stated ({data.working_capital}) differs from Current Assets - Current Liabilities ({calc_wc}).",
                    actual_value=str(data.working_capital),
                    expected_condition="working_capital == current_assets - short_term_liabilities"
                ))

        # 6. Extreme Outlier Check in Raw Ratios
        for attr_key, val in data.raw_ratios.items():
            if val is not None:
                # Extreme thresholds (e.g. > 10,000 or < -10,000)
                if abs(val) > 10000.0:
                    violations.append(DataQualityViolation(
                        field_name=attr_key,
                        flag_type=QualityFlagType.EXTREME_OUTLIER,
                        severity=Severity.INFO,
                        message=f"Ratio {attr_key} has an extreme value ({val:,.2f}), likely caused by near-zero denominator.",
                        actual_value=str(val),
                        expected_condition="abs(ratio) <= 10000"
                    ))

        return violations
