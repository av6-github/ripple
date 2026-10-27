"""
PostgreSQL Repository for Financial Records, SMEs, Ingestion Jobs, and Quality Flags
"""

import os
import json
import uuid
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import Json

from backend.domain.schemas import FinancialStatementData, DataQualityViolation
from backend.domain.enums import IngestionStatus
from backend.repositories.db_connection import connect_postgres


class FinancialRepository:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL or DATABASE_URL is not configured.")

    def _get_connection(self):
        return connect_postgres(self.db_url)

    def create_ingestion_job(
        self,
        file_name: str,
        file_type: str,
        file_size_bytes: int,
        storage_path: str,
        user_id: str,
        sme_id: Optional[str] = None
    ) -> str:
        job_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # Ensure user_id exists in app_user to satisfy foreign key constraint
                cursor.execute("SELECT id FROM app_user WHERE id = %s;", (user_id,))
                if not cursor.fetchone():
                    cursor.execute("SELECT id FROM app_user LIMIT 1;")
                    fallback = cursor.fetchone()
                    if fallback:
                        user_id = str(fallback[0])

                # Ensure sme_id exists in sme table if provided
                if sme_id:
                    cursor.execute("SELECT id FROM sme WHERE id = %s;", (sme_id,))
                    if not cursor.fetchone():
                        sme_id = None

                cursor.execute("""
                    INSERT INTO ingestion_job (
                        id, sme_id, user_id, file_name, file_type, file_size_bytes, storage_path, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (job_id, sme_id, user_id, file_name, file_type, file_size_bytes, storage_path, IngestionStatus.UPLOADED.value))
                conn.commit()
        return job_id

    def update_ingestion_job(
        self,
        job_id: str,
        status: IngestionStatus,
        extracted_data: Optional[Dict[str, Any]] = None,
        extraction_confidence: Optional[Dict[str, str]] = None,
        error_message: Optional[str] = None
    ):
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE ingestion_job
                    SET status = %s,
                        extracted_data = COALESCE(%s, extracted_data),
                        extraction_confidence = COALESCE(%s, extraction_confidence),
                        error_message = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                """, (
                    status.value,
                    Json(extracted_data) if extracted_data else None,
                    Json(extraction_confidence) if extraction_confidence else None,
                    error_message,
                    job_id
                ))
                conn.commit()

    def save_financial_record(
        self,
        sme_id: str,
        data: FinancialStatementData,
        completeness_pct: float = 100.0,
        forecasting_case: str = "ad_hoc"
    ) -> str:
        record_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO financial_record (
                        id, sme_id, fiscal_year, period_start_date, period_end_date, forecasting_case,
                        source_type, source_ref, confidence,
                        revenue, operating_expenses, ebit, ebitda, net_profit,
                        total_assets, current_assets, cash_and_equivalents, receivables,
                        inventory, fixed_assets, total_liabilities, short_term_liabilities,
                        long_term_liabilities, equity, working_capital,
                        raw_ratios, completeness_score
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s
                    );
                """, (
                    record_id, sme_id, data.fiscal_year, data.period_start_date, data.period_end_date, forecasting_case,
                    data.source_type.value, data.source_ref, data.confidence.value,
                    data.revenue, data.operating_expenses, data.ebit, data.ebitda, data.net_profit,
                    data.total_assets, data.current_assets, data.cash_and_equivalents, data.receivables,
                    data.inventory, data.fixed_assets, data.total_liabilities, data.short_term_liabilities,
                    data.long_term_liabilities, data.equity, data.working_capital,
                    Json(data.raw_ratios), completeness_pct
                ))
                conn.commit()
        return record_id

    def save_quality_flags(
        self,
        sme_id: str,
        record_id: str,
        violations: List[DataQualityViolation]
    ):
        if not violations:
            return
            
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for v in violations:
                    cursor.execute("""
                        INSERT INTO data_quality_flag (
                            id, sme_id, record_id, record_type, field_name, flag_type, severity, message, actual_value, expected_condition
                        ) VALUES (%s, %s, %s, 'financial', %s, %s, %s, %s, %s, %s);
                    """, (
                        str(uuid.uuid4()), sme_id, record_id, v.field_name, v.flag_type.value, v.severity.value,
                        v.message, v.actual_value, v.expected_condition
                    ))
                conn.commit()
