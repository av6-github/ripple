"""Tests for Point-in-Time (PIT) As-Of Joins and Look-Ahead Bias Prevention."""

from datetime import date
import pandas as pd
import pytest
from backend.features.domain import TargetLeakageError
from backend.quant.pit_join import AsOfJoinEngine, PointInTimeRecord


def test_pit_record_validation():
    """Ensure publication date cannot precede accounting period end date."""
    # Valid: Published after period end
    rec = PointInTimeRecord(
        entity_id="PL-001",
        period_end_date=date(2023, 12, 31),
        publication_date=date(2024, 2, 15),
        data={"revenue": 1000000},
    )
    assert rec.entity_id == "PL-001"

    # Invalid: Published before period end
    with pytest.raises(ValueError, match="cannot precede"):
        PointInTimeRecord(
            entity_id="PL-001",
            period_end_date=date(2023, 12, 31),
            publication_date=date(2023, 11, 15),
            data={"revenue": 1000000},
        )


def test_as_of_match_excludes_future_filings():
    """Verify that filings published after decision date are strictly excluded."""
    records = [
        PointInTimeRecord(
            entity_id="PL-001",
            period_end_date=date(2022, 12, 31),
            publication_date=date(2023, 2, 20),
            data={"period": "2022_FY", "revenue": 800000},
        ),
        PointInTimeRecord(
            entity_id="PL-001",
            period_end_date=date(2023, 12, 31),
            publication_date=date(2024, 2, 28),
            data={"period": "2023_FY", "revenue": 1200000},
        ),
    ]

    # Lending Decision made on 2024-01-15 (Before 2023 FY statement is legally filed)
    decision_date = date(2024, 1, 15)
    res = AsOfJoinEngine.match_as_of(records, as_of_date=decision_date, entity_id="PL-001")

    assert res.is_point_in_time_compliant is True
    assert res.discarded_future_records == 1  # 2023 FY statement discarded
    assert res.matched_record is not None
    assert res.matched_record.data["period"] == "2022_FY"
    assert res.matched_record.data["revenue"] == 800000

    # Decision made on 2024-03-01 (After 2023 FY statement is filed)
    res_later = AsOfJoinEngine.match_as_of(records, as_of_date=date(2024, 3, 1), entity_id="PL-001")
    assert res_later.discarded_future_records == 0
    assert res_later.matched_record is not None
    assert res_later.matched_record.data["period"] == "2023_FY"


def test_join_as_of_dataframe_enforces_no_leakage():
    """Verify pandas as_of join preserves backward causality."""
    decisions = pd.DataFrame(
        {
            "sme_id": ["SME-1", "SME-1"],
            "decision_date": ["2023-06-01", "2024-06-01"],
            "loan_amount": [50000, 100000],
        }
    )

    filings = pd.DataFrame(
        {
            "sme_id": ["SME-1", "SME-1"],
            "pub_date": ["2023-03-15", "2024-03-15"],
            "latest_ebitda": [12000, 24000],
        }
    )

    merged = AsOfJoinEngine.join_as_of_dataframe(
        left_df=decisions,
        right_df=filings,
        on_entity="sme_id",
        left_time_col="decision_date",
        right_time_col="pub_date",
    )

    assert len(merged) == 2
    # On 2023-06-01, matched 2023-03-15 filing (12000)
    assert merged.loc[0, "latest_ebitda"] == 12000
    # On 2024-06-01, matched 2024-03-15 filing (24000)
    assert merged.loc[1, "latest_ebitda"] == 24000
