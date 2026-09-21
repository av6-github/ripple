"""Domain schemas and errors for the RIPPLE Feature Engine."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TargetLeakageError(ValueError):
    """Raised when an input contains forbidden post-prediction information."""
    pass


class FinancialStatementPeriod(BaseModel):
    """Financial statement data for a single annual/quarterly period."""
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    fiscal_year: Optional[int] = None
    
    # Balance Sheet - Assets
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    marketable_securities: Optional[float] = 0.0
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    fixed_assets: Optional[float] = None
    
    # Balance Sheet - Liabilities & Equity
    total_liabilities: Optional[float] = None
    short_term_liabilities: Optional[float] = None
    long_term_liabilities: Optional[float] = None
    accounts_payable: Optional[float] = None
    total_equity: Optional[float] = None
    retained_earnings: Optional[float] = None
    share_capital: Optional[float] = None
    
    # Income Statement
    total_revenue: Optional[float] = None
    cost_of_goods_sold: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_profit_ebit: Optional[float] = None
    ebitda: Optional[float] = None
    depreciation_amortization: Optional[float] = 0.0
    interest_expense: Optional[float] = 0.0
    net_profit: Optional[float] = None
    
    # Cash Flow Statement
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None


class TransactionRecord(BaseModel):
    """Individual banking transaction record."""
    transaction_date: date
    amount: float
    direction: str = "credit"  # "credit" (inflow) or "debit" (outflow)
    category: Optional[str] = None


class InvoiceRecord(BaseModel):
    """Commercial invoice payment record."""
    invoice_id: str
    issue_date: date
    due_date: date
    payment_date: Optional[date] = None
    amount: float
    status: str = "paid"  # "paid", "open", "disputed"


class CounterpartyRelationship(BaseModel):
    """Commercial counterparty connection."""
    counterparty_id: str
    counterparty_name: str
    relationship_type: str  # "customer", "supplier", "partner"
    annual_volume: float
    tenure_months: int = 0
    is_synthetic: bool = False


class AlternativeDataInput(BaseModel):
    """Alternative data package for SME assessment."""
    transactions: List[TransactionRecord] = Field(default_factory=list)
    invoices: List[InvoiceRecord] = Field(default_factory=list)
    counterparties: List[CounterpartyRelationship] = Field(default_factory=list)


@dataclass
class FeatureEngineResult:
    """Standardized output of the FeatureEngine."""
    # Calculated feature dictionary matching docs/FEATURE_DICTIONARY.md
    features: Dict[str, Optional[float]] = field(default_factory=dict)
    
    # Quality & distress flags
    flags: Dict[str, bool] = field(default_factory=dict)
    
    # Human-readable indicators for UI / report
    indicators: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Completeness ratio of calculated features
    feature_completeness: float = 0.0
