"""
Ingestion Service (SRS FR-02, FR-03, and §7)
Orchestrates file validation, parser selection, validation, completeness checks, and persistence.
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from backend.domain.schemas import FinancialStatementData, IngestionResult, CompletenessEvaluation
from backend.domain.enums import IngestionStatus, SourceType, Confidence
from backend.services.parsers.csv_parser import CSVParser
from backend.services.parsers.xlsx_parser import XLSXParser
from backend.services.parsers.pdf_parser import PDFParser
from backend.services.parsers.arff_parser import ARFFParser
from backend.services.validation_service import ValidationEngine
from backend.services.completeness_service import CompletenessEvaluator
from backend.repositories.financial_repository import FinancialRepository

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB (ING-005)
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf", ".arff"}


class IngestionService:
    def __init__(self, repository: Optional[FinancialRepository] = None):
        self.repository = repository

    def process_file_upload(
        self,
        file_name: str,
        content: bytes,
        user_id: str,
        sme_id: Optional[str] = None
    ) -> IngestionResult:
        file_size = len(content)
        ext = Path(file_name).suffix.lower()

        # ING-005: File size check
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit of 10 MB.")

        # ING-004: Extension check
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

        # Initialize job if repository available
        job_id = "local-job"
        if self.repository:
            job_id = self.repository.create_ingestion_job(
                file_name=file_name,
                file_type=ext.lstrip('.'),
                file_size_bytes=file_size,
                storage_path=f"uploads/{file_name}",
                user_id=user_id,
                sme_id=sme_id
            )

        try:
            # Route to parser
            extraction_conf: Dict[str, str] = {}
            if ext == ".csv":
                financial_data, extraction_conf, _ = CSVParser.parse_content(content, source_ref=file_name)
            elif ext in {".xlsx", ".xls"}:
                financial_data, extraction_conf, _ = XLSXParser.parse_content(content, source_ref=file_name)
            elif ext == ".pdf":
                financial_data, extraction_conf, _ = PDFParser.parse_content(content, source_ref=file_name)
            elif ext == ".arff":
                # For ARFF, write temporary file and parse first instance
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".arff", delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                try:
                    records = ARFFParser.parse_file(tmp_path, source_ref=file_name)
                    financial_data = records[0] if records else FinancialStatementData(
                        source_type=SourceType.PUBLIC_DATASET,
                        source_ref=file_name,
                        confidence=Confidence.MISSING
                    )
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            else:
                raise ValueError(f"No parser available for {ext}")

            # Run Validation Engine (FR-03)
            quality_violations = ValidationEngine.validate(financial_data)

            # Run Completeness Evaluator (§7)
            completeness = CompletenessEvaluator.evaluate(financial_data)

            # Persist if repository and sme_id provided
            if self.repository and sme_id:
                record_id = self.repository.save_financial_record(
                    sme_id=sme_id,
                    data=financial_data,
                    completeness_pct=completeness.completeness_score_pct
                )
                self.repository.save_quality_flags(
                    sme_id=sme_id,
                    record_id=record_id,
                    violations=quality_violations
                )
                self.repository.update_ingestion_job(
                    job_id=job_id,
                    status=IngestionStatus.COMPLETED,
                    extracted_data=financial_data.model_dump(mode="json"),
                    extraction_confidence=extraction_conf
                )

            return IngestionResult(
                job_id=job_id,
                file_name=file_name,
                file_type=ext.lstrip('.'),
                file_size_bytes=file_size,
                status=IngestionStatus.COMPLETED,
                financial_data=financial_data,
                extraction_confidence=extraction_conf,
                quality_flags=quality_violations,
                completeness=completeness
            )

        except Exception as e:
            if self.repository:
                self.repository.update_ingestion_job(
                    job_id=job_id,
                    status=IngestionStatus.FAILED,
                    error_message=str(e)
                )
            raise

    @staticmethod
    def apply_manual_entry(
        existing_data: FinancialStatementData,
        manual_fields: Dict[str, float],
        officer_or_user_id: str
    ) -> FinancialStatementData:
        """
        T2.6: Applies manual overrides/corrections with mandatory manual_entry provenance (Rule 4.3).
        """
        data_dict = existing_data.model_dump()
        for field, val in manual_fields.items():
            if field in data_dict:
                data_dict[field] = val

        # Retain explicit manual provenance
        data_dict["source_type"] = SourceType.MANUAL_ENTRY
        data_dict["source_ref"] = f"manual_correction_by_{officer_or_user_id}"
        data_dict["confidence"] = Confidence.UNVERIFIED

        return FinancialStatementData(**data_dict)
