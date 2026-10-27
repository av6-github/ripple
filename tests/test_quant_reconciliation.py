"""Tests for Dual-Source Data Reconciliation with Tolerance-Based Checks."""

from backend.quant.reconciliation import (
    DataReconciliationService,
    ReconciliationStatus,
)


def test_reconciliation_pass_within_tolerance():
    """Verify that small rounding variations (<5%) pass without breach."""
    source_a = {
        "revenue": 1000000.0,
        "total_assets": 500000.0,
        "net_income": 80000.0,
    }
    source_b = {
        "revenue": 1020000.0,  # 1.96% difference
        "total_assets": 498000.0,  # 0.4% difference
        "net_income": 81000.0,  # 1.23% difference
    }

    result = DataReconciliationService.reconcile(
        source_a=source_a,
        source_b=source_b,
        source_a_name="Borrower Portal",
        source_b_name="KRS Polish Registry",
    )

    assert result.status == ReconciliationStatus.RECONCILED
    assert result.breached_fields_count == 0
    assert result.total_fields_compared == 3
    assert result.max_divergence_pct < 5.0


def test_reconciliation_detects_tolerance_breach():
    """Verify that discrepancies exceeding 5% tolerance trigger breach status."""
    source_a = {
        "revenue": 1000000.0,  # Borrower claims 1,000,000
        "net_income": 120000.0,
    }
    source_b = {
        "revenue": 750000.0,  # Official registry shows only 750,000 (25% breach!)
        "net_income": 118000.0,
    }

    result = DataReconciliationService.reconcile(source_a, source_b)

    assert result.status == ReconciliationStatus.TOLERANCE_BREACH
    assert result.breached_fields_count >= 1

    rev_item = next(i for i in result.items if i.field_name == "revenue")
    assert rev_item.is_breach is True
    assert rev_item.relative_divergence_pct == 25.0
    assert "BREACH" in result.audit_notes[0]


def test_reconciliation_handles_missing_sources():
    """Verify graceful handling when one source is empty or missing."""
    result = DataReconciliationService.reconcile({}, {"revenue": 500000})
    assert result.status == ReconciliationStatus.SOURCE_MISSING
