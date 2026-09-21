"""
Parser for Structured Financial CSV Files with Smart Synonym Mapping
"""

import io
import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from backend.domain.schemas import FinancialStatementData
from backend.domain.enums import SourceType, Confidence


HEADER_MAPPINGS = {
    "revenue": [
        "revenue", "sales", "total_revenue", "total_sales", "turnover", "gross_revenue", "net_sales"
    ],
    "operating_expenses": [
        "operating_expenses", "opex", "operating_exp", "total_operating_expenses"
    ],
    "ebit": [
        "ebit", "operating_profit", "operating_income", "profit_before_interest_and_tax"
    ],
    "ebitda": [
        "ebitda", "operating_profit_before_depreciation"
    ],
    "net_profit": [
        "net_profit", "net_income", "profit_after_tax", "pat", "bottom_line"
    ],
    "total_assets": [
        "total_assets", "assets", "total_asset"
    ],
    "current_assets": [
        "current_assets", "ca", "short_term_assets"
    ],
    "cash_and_equivalents": [
        "cash", "cash_and_equivalents", "cash_and_bank", "bank_balance", "cash_equivalents"
    ],
    "receivables": [
        "receivables", "accounts_receivable", "debtors", "trade_receivables", "ar"
    ],
    "inventory": [
        "inventory", "inventories", "stock", "closing_stock"
    ],
    "fixed_assets": [
        "fixed_assets", "non_current_assets", "ppe", "property_plant_equipment"
    ],
    "total_liabilities": [
        "total_liabilities", "liabilities", "total_debt_and_liabilities"
    ],
    "short_term_liabilities": [
        "short_term_liabilities", "current_liabilities", "cl", "short_term_debt"
    ],
    "long_term_liabilities": [
        "long_term_liabilities", "non_current_liabilities", "long_term_debt"
    ],
    "equity": [
        "equity", "shareholders_equity", "net_worth", "book_equity", "total_equity"
    ],
    "working_capital": [
        "working_capital", "net_working_capital", "nwc"
    ]
}


def normalize_header(header: str) -> str:
    h = header.strip().lower()
    h = re.sub(r'[^a-z0-9]', '_', h)
    h = re.sub(r'_+', '_', h).strip('_')
    return h


class CSVParser:
    """Parses and maps structured CSV financial records to canonical schemas."""

    @staticmethod
    def parse_content(content: bytes, source_ref: str = "uploaded_file.csv") -> Tuple[FinancialStatementData, Dict[str, str], List[str]]:
        """
        Parses CSV bytes, returns (FinancialStatementData, extraction_confidence, unmapped_columns).
        """
        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Failed to read CSV content: {e}")

        if df.empty:
            raise ValueError("Uploaded CSV file is empty.")

        # If multiple rows, take the first/latest row for single-period assessment
        row = df.iloc[0]
        
        extracted_fields: Dict[str, Any] = {}
        extraction_confidence: Dict[str, str] = {}
        unmapped_cols: List[str] = []
        raw_ratios: Dict[str, Optional[float]] = {}

        # Reverse lookup map
        norm_to_canonical = {}
        for canonical, synonyms in HEADER_MAPPINGS.items():
            for syn in synonyms:
                norm_to_canonical[syn] = canonical

        for col in df.columns:
            norm_col = normalize_header(col)
            val = row[col]
            
            # Check for Polish ratio format (Attr1 - Attr64 or X1 - X64)
            match_attr = re.match(r'^(?:attr|x)(\d+)$', norm_col)
            if match_attr:
                idx = int(match_attr.group(1))
                if 1 <= idx <= 64:
                    attr_key = f"Attr{idx}"
                    raw_ratios[attr_key] = None if pd.isna(val) else float(val)
                    extraction_confidence[attr_key] = Confidence.VERIFIED.value
                    continue

            canonical_field = norm_to_canonical.get(norm_col)
            if canonical_field:
                if not pd.isna(val):
                    try:
                        clean_num = float(str(val).replace(',', '').replace('$', '').replace('€', '').strip())
                        extracted_fields[canonical_field] = clean_num
                        extraction_confidence[canonical_field] = Confidence.VERIFIED.value
                    except (ValueError, TypeError):
                        extracted_fields[canonical_field] = None
                        extraction_confidence[canonical_field] = Confidence.UNVERIFIED.value
                else:
                    extracted_fields[canonical_field] = None
                    extraction_confidence[canonical_field] = Confidence.MISSING.value
            else:
                unmapped_cols.append(col)

        # Mark all unencountered canonical fields as MISSING
        for canonical_field in HEADER_MAPPINGS.keys():
            if canonical_field not in extracted_fields:
                extracted_fields[canonical_field] = None
                extraction_confidence[canonical_field] = Confidence.MISSING.value

        stmt = FinancialStatementData(
            **extracted_fields,
            raw_ratios=raw_ratios,
            source_type=SourceType.EXTRACTED_FILE,
            source_ref=source_ref,
            confidence=Confidence.VERIFIED if any(v is not None for v in extracted_fields.values()) else Confidence.UNVERIFIED
        )
        
        return stmt, extraction_confidence, unmapped_cols
