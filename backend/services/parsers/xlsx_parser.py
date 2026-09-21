"""
Parser for Excel (XLSX/XLS) Financial Workbooks
"""

import io
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from backend.domain.schemas import FinancialStatementData
from backend.services.parsers.csv_parser import CSVParser


class XLSXParser:
    """Parses Excel workbooks and applies canonical financial mapping."""

    @staticmethod
    def parse_content(content: bytes, source_ref: str = "uploaded_file.xlsx") -> Tuple[FinancialStatementData, Dict[str, str], List[str]]:
        try:
            excel_file = io.BytesIO(content)
            # Read first sheet
            df = pd.read_excel(excel_file, engine="openpyxl")
        except Exception as e:
            raise ValueError(f"Failed to read Excel content: {e}")

        if df.empty:
            raise ValueError("Uploaded Excel workbook is empty.")

        # Convert to CSV buffer and delegate to canonical mapping logic
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        return CSVParser.parse_content(csv_buffer.getvalue(), source_ref=source_ref)
