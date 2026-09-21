"""
RIPPLE Domain Enums (Governed by AGENTS.md and SRS.md)
"""

from enum import Enum


class SourceType(str, Enum):
    """Allowed provenance source types (AGENTS.md Rule 4.3)"""
    EXTRACTED_FILE = "extracted_file"
    MANUAL_ENTRY = "manual_entry"
    PUBLIC_DATASET = "public_dataset"
    SYNTHETIC = "synthetic"
    DERIVED = "derived"


class Confidence(str, Enum):
    """Allowed confidence values (AGENTS.md Rule 4.3)"""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    ESTIMATED = "estimated"
    MISSING = "missing"


class RiskRecommendation(str, Enum):
    """Allowed system recommendations (AGENTS.md Rule 4.6)"""
    LOWER_RISK = "LOWER_RISK"
    FURTHER_REVIEW = "FURTHER_REVIEW"
    HIGHER_RISK = "HIGHER_RISK"
    INCONCLUSIVE = "INCONCLUSIVE"


class RelationshipType(str, Enum):
    """Supported graph edge types (SRS.md §9)"""
    SUPPLIES = "SUPPLIES"
    SELLS_TO = "SELLS_TO"
    TRANSACTS_WITH = "TRANSACTS_WITH"
    SHARES_DIRECTOR = "SHARES_DIRECTOR"


class ForecastingCase(str, Enum):
    """Polish Bankruptcy benchmark forecasting horizons (ADR-001)"""
    YEAR_1 = "1year"  # 5 years to bankruptcy
    YEAR_2 = "2year"  # 4 years to bankruptcy
    YEAR_3 = "3year"  # 3 years to bankruptcy
    YEAR_4 = "4year"  # 2 years to bankruptcy
    YEAR_5 = "5year"  # 1 year to bankruptcy
    AD_HOC = "ad_hoc"


class QualityFlagType(str, Enum):
    """Data quality violation types (SRS.md FR-03)"""
    INVALID_RANGE = "invalid_range"
    ACCOUNTING_INCONSISTENCY = "accounting_inconsistency"
    DUPLICATE_PERIOD = "duplicate_period"
    FUTURE_DATE = "future_date"
    SOURCE_CONFLICT = "source_conflict"
    MISSING_CRITICAL = "missing_critical"
    EXTREME_OUTLIER = "extreme_outlier"


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IngestionStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AppRole(str, Enum):
    """Application roles matching PostgreSQL RLS roles."""
    BANK_OFFICER = "bank_officer"
    SME_USER = "sme_user"
    ADMIN = "admin"

