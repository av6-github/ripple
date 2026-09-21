"""
Parser for Unstructured / Standard Financial Statement PDFs (SRS FR-02)
"""

import io
import re
from typing import Dict, Any, List, Optional, Tuple
from pypdf import PdfReader

from backend.domain.schemas import FinancialStatementData
from backend.domain.enums import SourceType, Confidence
from backend.services.parsers.csv_parser import HEADER_MAPPINGS


class PDFParser:
    """Extracts financial text and figures from PDF statements."""

    @staticmethod
    def parse_content(content: bytes, source_ref: str = "statement.pdf") -> Tuple[FinancialStatementData, Dict[str, str], List[str]]:
        try:
            reader = PdfReader(io.BytesIO(content))
            full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document: {e}")

        if not full_text.strip():
            raise ValueError("PDF contains no extractable text (scanned image or empty).")

        extracted_fields: Dict[str, Any] = {}
        extraction_confidence: Dict[str, str] = {}
        unmapped_signals: List[str] = []

        lines = full_text.splitlines()

        for canonical_field, synonyms in HEADER_MAPPINGS.items():
            pattern = re.compile(
                r'(?:' + '|'.join(re.escape(s.replace('_', ' ')) for s in synonyms) + r')[:\s\-–]+([\(]?[\$€£₹]?\s*[\d,]+(?:\.\d+)?[\)]?)',
                re.IGNORECASE
            )
            
            found = False
            for line in lines:
                m = pattern.search(line)
                if m:
                    num_str = m.group(1).strip()
                    # Handle negative accounting parentheses (e.g. (50,000) -> -50000)
                    is_neg = num_str.startswith('(') and num_str.endswith(')')
                    clean_num_str = re.sub(r'[^\d.]', '', num_str)
                    try:
                        val = float(clean_num_str)
                        if is_neg:
                            val = -val
                        extracted_fields[canonical_field] = val
                        extraction_confidence[canonical_field] = Confidence.VERIFIED.value
                        found = True
                        break
                    except ValueError:
                        pass
            
            if not found:
                extracted_fields[canonical_field] = None
                extraction_confidence[canonical_field] = Confidence.MISSING.value

        stmt = FinancialStatementData(
            **extracted_fields,
            raw_ratios={},
            source_type=SourceType.EXTRACTED_FILE,
            source_ref=source_ref,
            confidence=Confidence.VERIFIED if any(v is not None for v in extracted_fields.values()) else Confidence.MISSING
        )

        return stmt, extraction_confidence, unmapped_signals
