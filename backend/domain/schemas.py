"""
Pydantic v2 Schemas for RIPPLE Ingestion, Provenance, and Validation
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
import uuid

from backend.domain.enums import SourceType, Confidence, Severity, QualityFlagType, IngestionStatus


class ProvenancedField(BaseModel):
    """Encapsulates a factual value with mandatory provenance (Rule 4.3)"""
    value: Optional[float] = None
    source_type: SourceType
    source_ref: str
    confidence: Confidence = Confidence.UNVERIFIED


class FinancialStatementData(BaseModel):
    """Standardized financial statement items and raw canonical ratios"""
    fiscal_year: Optional[int] = None
    period_start_date: Optional[date] = None
    period_end_date: Optional[date] = None
    
    # Balance Sheet & Income Statement aggregates
    revenue: Optional[float] = None
    operating_expenses: Optional[float] = None
    ebit: Optional[float] = None
    ebitda: Optional[float] = None
    net_profit: Optional[float] = None
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    receivables: Optional[float] = None
    inventory: Optional[float] = None
    fixed_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    short_term_liabilities: Optional[float] = None
    long_term_liabilities: Optional[float] = None
    equity: Optional[float] = None
    working_capital: Optional[float] = None
    
    # Lossless storage for canonical 64 Polish bankruptcy ratios (Attr1 - Attr64)
    raw_ratios: Dict[str, Optional[float]] = Field(default_factory=dict)
    
    # Mandatory Provenance Metadata
    source_type: SourceType
    source_ref: str
    confidence: Confidence


class DataQualityViolation(BaseModel):
    field_name: str
    flag_type: QualityFlagType
    severity: Severity
    message: str
    actual_value: Optional[str] = None
    expected_condition: Optional[str] = None


class CompletenessEvaluation(BaseModel):
    completeness_score_pct: float
    is_conclusive: bool
    missing_critical_fields: List[str] = Field(default_factory=list)
    missing_optional_fields: List[str] = Field(default_factory=list)
    inconclusive_reason: Optional[str] = None


class IngestionResult(BaseModel):
    job_id: str
    file_name: str
    file_type: str
    file_size_bytes: int
    status: IngestionStatus
    financial_data: Optional[FinancialStatementData] = None
    extraction_confidence: Dict[str, str] = Field(default_factory=dict)
    quality_flags: List[DataQualityViolation] = Field(default_factory=list)
    completeness: Optional[CompletenessEvaluation] = None
    error_message: Optional[str] = None
