"""Dual-Source Data Reconciliation Service for RIPPLE.

Implements institutional quantitative data reconciliation between independent financial feeds:
- Primary Source (e.g. Borrower Portal self-reported financials / application form)
- Authoritative Verification Source (e.g. Polish KRS Court Register, VAT SAF-T / JPK_V7, or Open Banking)

Calculates dollar and relative divergence per line item, compares against policy tolerance thresholds,
and generates an audit report to protect lenders against fraudulent or erroneous filings.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReconciliationStatus(str, Enum):
    RECONCILED = "RECONCILED"
    TOLERANCE_BREACH = "TOLERANCE_BREACH"
    UNRECONCILED = "UNRECONCILED"
    SOURCE_MISSING = "SOURCE_MISSING"


@dataclass
class ReconciliationItem:
    """A reconciled individual line item with absolute and percentage divergence."""

    field_name: str
    source_a_value: Optional[float]
    source_b_value: Optional[float]
    source_a_label: str
    source_b_label: str
    absolute_difference: Optional[float]
    relative_divergence_pct: Optional[float]
    tolerance_threshold_pct: float
    is_breach: bool
    note: str = ""


@dataclass
class ReconciliationResult:
    """Institutional reconciliation summary across all compared accounting items."""

    status: ReconciliationStatus
    source_a_name: str
    source_b_name: str
    total_fields_compared: int
    breached_fields_count: int
    max_divergence_pct: float
    items: List[ReconciliationItem] = field(default_factory=list)
    audit_notes: List[str] = field(default_factory=list)


class DataReconciliationService:
    """Tolerance-based reconciliation engine comparing multi-source corporate disclosures."""

    DEFAULT_TOLERANCE_PCT: float = 5.0  # 5% relative variance allowance

    # Field mapping dictionary: canonical name -> alternate field names in source feeds
    CANONICAL_FIELDS: Dict[str, List[str]] = {
        "revenue": ["revenue", "sales", "turnover", "total_revenue"],
        "net_income": ["net_income", "net_profit", "profit_loss"],
        "total_assets": ["total_assets", "assets", "balance_sheet_total"],
        "total_liabilities": ["total_liabilities", "liabilities", "total_debt"],
        "cash_and_equivalents": ["cash", "cash_and_equivalents", "bank_balances"],
        "short_term_liabilities": ["short_term_liabilities", "current_liabilities"],
        "equity": ["equity", "total_equity", "shareholders_equity"],
    }

    @classmethod
    def reconcile(
        cls,
        source_a: Dict[str, Any],
        source_b: Dict[str, Any],
        source_a_name: str = "Borrower Self-Reported",
        source_b_name: str = "National Registry (KRS/VAT)",
        custom_tolerances: Optional[Dict[str, float]] = None,
    ) -> ReconciliationResult:
        """Execute tolerance-based dual-source reconciliation.

        Parameters
        ----------
        source_a : Dict[str, Any]
            First financial disclosure dictionary.
        source_b : Dict[str, Any]
            Second financial disclosure dictionary.
        source_a_name : str
            Display label for first source.
        source_b_name : str
            Display label for second source.
        custom_tolerances : Optional[Dict[str, float]]
            Optional override of tolerance per field in percent (e.g. {"revenue": 3.0}).

        Returns
        -------
        ReconciliationResult
            Structured reconciliation audit object.
        """
        if not source_a or not source_b:
            return ReconciliationResult(
                status=ReconciliationStatus.SOURCE_MISSING,
                source_a_name=source_a_name,
                source_b_name=source_b_name,
                total_fields_compared=0,
                breached_fields_count=0,
                max_divergence_pct=0.0,
                items=[],
                audit_notes=["One or both data sources are empty or missing."],
            )

        items: List[ReconciliationItem] = []
        max_div: float = 0.0
        breach_count: int = 0
        audit_notes: List[str] = []

        tolerances = custom_tolerances or {}

        for canonical_name, aliases in cls.CANONICAL_FIELDS.items():
            val_a = cls._extract_val(source_a, aliases)
            val_b = cls._extract_val(source_b, aliases)

            tol = tolerances.get(canonical_name, cls.DEFAULT_TOLERANCE_PCT)

            if val_a is None and val_b is None:
                continue

            if val_a is None or val_b is None:
                # One source has the line item while the other is missing
                item = ReconciliationItem(
                    field_name=canonical_name,
                    source_a_value=val_a,
                    source_b_value=val_b,
                    source_a_label=source_a_name,
                    source_b_label=source_b_name,
                    absolute_difference=None,
                    relative_divergence_pct=None,
                    tolerance_threshold_pct=tol,
                    is_breach=True,
                    note=f"Asymmetric line item: Present in {'Source A' if val_a is not None else 'Source B'} only.",
                )
                items.append(item)
                breach_count += 1
                audit_notes.append(f"MISSING_FIELD: {canonical_name} is only present in one source.")
                continue

            abs_diff = abs(val_a - val_b)
            denom = max(abs(val_a), abs(val_b))

            if denom < 1e-6:
                rel_div = 0.0
            else:
                rel_div = round((abs_diff / denom) * 100.0, 2)

            is_breach = rel_div > tol
            if is_breach:
                breach_count += 1
                audit_notes.append(
                    f"BREACH: {canonical_name} diverged by {rel_div}% "
                    f"({source_a_name}: {val_a:,.2f} vs {source_b_name}: {val_b:,.2f}), "
                    f"exceeding {tol}% tolerance."
                )

            max_div = max(max_div, rel_div)

            items.append(
                ReconciliationItem(
                    field_name=canonical_name,
                    source_a_value=val_a,
                    source_b_value=val_b,
                    source_a_label=source_a_name,
                    source_b_label=source_b_name,
                    absolute_difference=round(abs_diff, 2),
                    relative_divergence_pct=rel_div,
                    tolerance_threshold_pct=tol,
                    is_breach=is_breach,
                    note="Within acceptable tolerance." if not is_breach else f"Exceeds {tol}% tolerance threshold.",
                )
            )

        if not items:
            status = ReconciliationStatus.UNRECONCILED
            audit_notes.append("No matching canonical financial fields found across sources.")
        elif breach_count > 0:
            status = ReconciliationStatus.TOLERANCE_BREACH
        else:
            status = ReconciliationStatus.RECONCILED
            audit_notes.append("All reported line items reconciled within policy tolerance limits.")

        return ReconciliationResult(
            status=status,
            source_a_name=source_a_name,
            source_b_name=source_b_name,
            total_fields_compared=len(items),
            breached_fields_count=breach_count,
            max_divergence_pct=max_div,
            items=items,
            audit_notes=audit_notes,
        )

    @staticmethod
    def _extract_val(data: Dict[str, Any], aliases: List[str]) -> Optional[float]:
        for k in aliases:
            if k in data and data[k] is not None:
                try:
                    return float(data[k])
                except (ValueError, TypeError):
                    continue
            # Case insensitive check
            for actual_key, val in data.items():
                if actual_key.lower().strip() == k.lower().strip() and val is not None:
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        continue
        return None
