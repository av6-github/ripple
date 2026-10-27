"""Tests for Automated Data Quality & Balance Sheet Identity Gate."""

from backend.quant.data_quality import DataQualityGate, QualityStatus


def test_balanced_statement_passes_quality_gate():
    """Verify clean, balanced accounting inputs achieve 100% quality score."""
    stmt = {
        "total_assets": 1000000.0,
        "total_liabilities": 600000.0,
        "equity": 400000.0,  # 600k + 400k = 1000k (exact balance)
        "revenue": 1500000.0,
        "current_assets": 400000.0,
        "short_term_liabilities": 250000.0,
        "working_capital": 150000.0,  # 400k - 250k = 150k
    }

    report = DataQualityGate.evaluate(stmt)

    assert report.overall_status == QualityStatus.PASSED
    assert report.quality_score == 100.0
    assert report.failed_count == 0


def test_severe_imbalance_fails_quality_gate():
    """Verify that an imbalanced balance sheet ($Assets != Liab + Equity) triggers FAILED status."""
    fraudulent_or_corrupt_stmt = {
        "total_assets": 1000000.0,
        "total_liabilities": 200000.0,
        "equity": 100000.0,  # Total Liab + Eq is 300k, missing 700k!
        "revenue": 500000.0,
    }

    report = DataQualityGate.evaluate(fraudulent_or_corrupt_stmt)

    assert report.overall_status == QualityStatus.FAILED
    assert report.failed_count >= 1

    bs_check = next(c for c in report.checks if c.check_name == "Balance Sheet Identity")
    assert bs_check.status == QualityStatus.FAILED
    assert "Severe balance sheet breach" in bs_check.message


def test_negative_revenue_fails_sanity():
    """Verify negative revenue is caught by range sanity checks."""
    stmt = {
        "total_assets": 500000.0,
        "total_liabilities": 300000.0,
        "equity": 200000.0,
        "revenue": -50000.0,  # Impossible negative top-line
    }

    report = DataQualityGate.evaluate(stmt)
    assert report.overall_status == QualityStatus.FAILED
    rev_check = next(c for c in report.checks if c.check_name == "Non-Negative Revenue")
    assert rev_check.status == QualityStatus.FAILED
