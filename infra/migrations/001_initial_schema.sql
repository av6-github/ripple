-- RIPPLE PostgreSQL Initial Schema Migration
-- Version: 001_initial_schema.sql
-- Description: Core domain schema for SME credit risk assessment, provenance, multi-horizon predictions, and auditability.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. APP USERS (Syncs with Supabase auth.users)
-- =============================================================================
CREATE TABLE IF NOT EXISTS app_user (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('bank_officer', 'sme_user', 'admin')),
    first_name TEXT,
    last_name TEXT,
    organization TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 2. SME / COMPANY IDENTITY
-- =============================================================================
CREATE TABLE IF NOT EXISTS sme (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name TEXT NOT NULL,
    registration_number TEXT UNIQUE,
    tax_id TEXT UNIQUE,
    industry TEXT NOT NULL,
    sector TEXT,
    business_age_years NUMERIC(5, 2),
    location TEXT,
    city TEXT,
    country TEXT DEFAULT 'PL',
    business_type TEXT,
    user_id UUID REFERENCES app_user(id) ON DELETE SET NULL,
    is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sme_legal_name ON sme (legal_name);
CREATE INDEX IF NOT EXISTS idx_sme_user_id ON sme (user_id);
CREATE INDEX IF NOT EXISTS idx_sme_is_synthetic ON sme (is_synthetic);

-- =============================================================================
-- 3. FINANCIAL RECORDS (Observations & Canonical Ratios)
-- =============================================================================
CREATE TABLE IF NOT EXISTS financial_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sme_id UUID NOT NULL REFERENCES sme(id) ON DELETE CASCADE,
    fiscal_year INTEGER,
    period_start_date DATE,
    period_end_date DATE,
    reporting_period TEXT DEFAULT 'annual' CHECK (reporting_period IN ('annual', 'semi_annual', 'quarterly', 'ad_hoc')),
    forecasting_case TEXT CHECK (forecasting_case IN ('1year', '2year', '3year', '4year', '5year', 'ad_hoc')),
    
    -- Mandatory Provenance Fields (Rule 4.3)
    source_type TEXT NOT NULL CHECK (source_type IN ('extracted_file', 'manual_entry', 'public_dataset', 'synthetic', 'derived')),
    source_ref TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('verified', 'unverified', 'estimated', 'missing')),
    
    -- Target Outcome (Optional in live underwriting; populated for benchmark/evaluation)
    target_bankruptcy BOOLEAN,
    target_horizon_months INTEGER CHECK (target_horizon_months IN (12, 24, 36, 48, 60)),
    
    -- Core Statement Items (Reconstructed/Extracted where available)
    revenue NUMERIC(18, 4),
    operating_expenses NUMERIC(18, 4),
    ebit NUMERIC(18, 4),
    ebitda NUMERIC(18, 4),
    net_profit NUMERIC(18, 4),
    total_assets NUMERIC(18, 4),
    current_assets NUMERIC(18, 4),
    cash_and_equivalents NUMERIC(18, 4),
    receivables NUMERIC(18, 4),
    inventory NUMERIC(18, 4),
    fixed_assets NUMERIC(18, 4),
    total_liabilities NUMERIC(18, 4),
    short_term_liabilities NUMERIC(18, 4),
    long_term_liabilities NUMERIC(18, 4),
    equity NUMERIC(18, 4),
    working_capital NUMERIC(18, 4),
    
    -- Raw Canonical Polish Dataset Ratios (X1 through X64 stored losslessly)
    raw_ratios JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    completeness_score NUMERIC(5, 2) DEFAULT 100.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_financial_record_sme_id ON financial_record (sme_id);
CREATE INDEX IF NOT EXISTS idx_financial_record_forecasting_case ON financial_record (forecasting_case);
CREATE INDEX IF NOT EXISTS idx_financial_record_source_type ON financial_record (source_type);

-- =============================================================================
-- 4. ALTERNATIVE DATA RECORDS
-- =============================================================================
CREATE TABLE IF NOT EXISTS alternative_data_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sme_id UUID NOT NULL REFERENCES sme(id) ON DELETE CASCADE,
    observation_date DATE NOT NULL,
    
    -- Mandatory Provenance Fields (Rule 4.3)
    source_type TEXT NOT NULL CHECK (source_type IN ('extracted_file', 'manual_entry', 'public_dataset', 'synthetic', 'derived')),
    source_ref TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('verified', 'unverified', 'estimated', 'missing')),
    
    -- Behavioral Metrics
    transaction_frequency_monthly NUMERIC(10, 2),
    transaction_volume_monthly NUMERIC(18, 2),
    avg_transaction_size NUMERIC(18, 2),
    transaction_size_volatility NUMERIC(10, 4),
    payment_timeliness_score NUMERIC(5, 2),
    payment_delay_days_avg NUMERIC(6, 2),
    payment_delay_trend TEXT CHECK (payment_delay_trend IN ('improving', 'stable', 'deteriorating')),
    customer_concentration_pct NUMERIC(5, 2),
    supplier_concentration_pct NUMERIC(5, 2),
    relationship_stability_months INTEGER,
    
    metadata JSONB DEFAULT '{}'::jsonb,
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alternative_data_sme_id ON alternative_data_record (sme_id);

-- =============================================================================
-- 5. RELATIONSHIPS (Commercial Graph Edges - PostgreSQL Source of Truth)
-- =============================================================================
CREATE TABLE IF NOT EXISTS relationship (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_sme_id UUID NOT NULL REFERENCES sme(id) ON DELETE CASCADE,
    target_sme_id UUID NOT NULL REFERENCES sme(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('SUPPLIES', 'SELLS_TO', 'TRANSACTS_WITH', 'SHARES_DIRECTOR')),
    weight NUMERIC(10, 4) DEFAULT 1.0,
    transaction_volume_annual NUMERIC(18, 2),
    relationship_duration_months INTEGER,
    
    -- Mandatory Synthetic & Provenance Flags (Rule 4.3, 4.4)
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
    source_type TEXT NOT NULL CHECK (source_type IN ('extracted_file', 'manual_entry', 'public_dataset', 'synthetic', 'derived')),
    source_ref TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('verified', 'unverified', 'estimated', 'missing')),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_no_self_relationship CHECK (source_sme_id <> target_sme_id)
);

CREATE INDEX IF NOT EXISTS idx_relationship_source ON relationship (source_sme_id);
CREATE INDEX IF NOT EXISTS idx_relationship_target ON relationship (target_sme_id);
CREATE INDEX IF NOT EXISTS idx_relationship_type ON relationship (relationship_type);

-- =============================================================================
-- 6. DATA QUALITY FLAGS
-- =============================================================================
CREATE TABLE IF NOT EXISTS data_quality_flag (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sme_id UUID NOT NULL REFERENCES sme(id) ON DELETE CASCADE,
    record_id UUID,
    record_type TEXT NOT NULL CHECK (record_type IN ('financial', 'alternative', 'relationship')),
    field_name TEXT NOT NULL,
    flag_type TEXT NOT NULL CHECK (flag_type IN ('invalid_range', 'accounting_inconsistency', 'duplicate_period', 'future_date', 'source_conflict', 'missing_critical', 'extreme_outlier')),
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
    message TEXT NOT NULL,
    actual_value TEXT,
    expected_condition TEXT,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dq_sme_id ON data_quality_flag (sme_id);
CREATE INDEX IF NOT EXISTS idx_dq_severity ON data_quality_flag (severity);

-- =============================================================================
-- 7. MODEL REGISTRY
-- =============================================================================
CREATE TABLE IF NOT EXISTS model_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL UNIQUE,
    model_type TEXT NOT NULL CHECK (model_type IN ('tabular_xgboost', 'tabular_baseline', 'gnn_graphsage', 'risk_fusion')),
    target_horizon_months INTEGER NOT NULL CHECK (target_horizon_months IN (9, 12, 18, 24, 36, 48, 60)),
    artefact_uri TEXT NOT NULL,
    hyperparameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    feature_names JSONB NOT NULL DEFAULT '[]'::jsonb,
    training_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    calibration_method TEXT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_registry_active ON model_registry (is_active);

-- =============================================================================
-- 8. ASSESSMENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS assessment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sme_id UUID NOT NULL REFERENCES sme(id) ON DELETE CASCADE,
    officer_id UUID NOT NULL REFERENCES app_user(id),
    assessment_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'INCONCLUSIVE', 'FAILED')),
    inconclusive_reason TEXT,
    data_completeness_pct NUMERIC(5, 2),
    overall_confidence TEXT CHECK (overall_confidence IN ('verified', 'unverified', 'estimated', 'insufficient')),
    
    -- Responsible Officer Lending Decision (Rule 4.6)
    officer_decision TEXT CHECK (officer_decision IN ('APPROVE', 'REJECT', 'FURTHER_REVIEW', 'OVERRIDE_APPROVE', 'OVERRIDE_REJECT')),
    officer_notes TEXT,
    officer_decision_date TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assessment_sme_id ON assessment (sme_id);
CREATE INDEX IF NOT EXISTS idx_assessment_officer_id ON assessment (officer_id);
CREATE INDEX IF NOT EXISTS idx_assessment_status ON assessment (status);

-- =============================================================================
-- 9. ASSESSMENT INPUT SNAPSHOT (Historical Reproducibility - Rule 17)
-- =============================================================================
CREATE TABLE IF NOT EXISTS assessment_input_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL UNIQUE REFERENCES assessment(id) ON DELETE CASCADE,
    financial_features_snapshot JSONB NOT NULL,
    alternative_features_snapshot JSONB NOT NULL,
    graph_features_snapshot JSONB NOT NULL,
    provenance_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 10. PREDICTIONS (Multi-Branch & Multi-Horizon)
-- =============================================================================
CREATE TABLE IF NOT EXISTS prediction (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES assessment(id) ON DELETE CASCADE,
    model_version TEXT NOT NULL REFERENCES model_registry(model_version),
    horizon_months INTEGER NOT NULL CHECK (horizon_months IN (9, 12, 18, 24, 36, 48, 60)),
    
    -- Distinct Risk Branches (SRS FR-07)
    tabular_pd NUMERIC(6, 5),
    graph_pd NUMERIC(6, 5),
    fused_pd NUMERIC(6, 5),
    calibrated_pd NUMERIC(6, 5),
    
    risk_band TEXT CHECK (risk_band IN ('LOW', 'MEDIUM_LOW', 'MEDIUM', 'MEDIUM_HIGH', 'HIGH', 'VERY_HIGH', 'INCONCLUSIVE')),
    recommendation TEXT CHECK (recommendation IN ('LOWER_RISK', 'FURTHER_REVIEW', 'HIGHER_RISK', 'INCONCLUSIVE')),
    uncertainty_score NUMERIC(6, 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prediction_assessment_id ON prediction (assessment_id);

-- =============================================================================
-- 11. EXPLANATIONS (SHAP for Tabular Branch - Rule 4.7)
-- =============================================================================
CREATE TABLE IF NOT EXISTS explanation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES prediction(id) ON DELETE CASCADE,
    explainer_type TEXT NOT NULL DEFAULT 'SHAP_TreeExplainer',
    base_value NUMERIC(10, 6) NOT NULL,
    top_risk_increasing_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    top_risk_reducing_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    full_shap_values JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_explanation_prediction_id ON explanation (prediction_id);

-- =============================================================================
-- 12. SCENARIO RESULTS (What-If Stress Testing - SRS FR-09)
-- =============================================================================
CREATE TABLE IF NOT EXISTS scenario_result (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES assessment(id) ON DELETE CASCADE,
    scenario_name TEXT NOT NULL,
    scenario_type TEXT NOT NULL CHECK (scenario_type IN ('predefined', 'custom')),
    stress_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    base_pd NUMERIC(6, 5) NOT NULL,
    stressed_pd NUMERIC(6, 5) NOT NULL,
    pd_delta NUMERIC(6, 5) NOT NULL,
    stressed_risk_band TEXT NOT NULL,
    disclaimer TEXT NOT NULL DEFAULT 'Model-based estimate, not a forecast, not causal.',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scenario_result_assessment ON scenario_result (assessment_id);

-- =============================================================================
-- 13. INGESTION JOBS (File Parsing Pipeline - SRS FR-02)
-- =============================================================================
CREATE TABLE IF NOT EXISTS ingestion_job (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sme_id UUID REFERENCES sme(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES app_user(id),
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('csv', 'xlsx', 'pdf', 'arff', 'json')),
    file_size_bytes BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('UPLOADED', 'PARSING', 'VALIDATING', 'COMPLETED', 'FAILED')),
    extracted_data JSONB DEFAULT '{}'::jsonb,
    extraction_confidence JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_job_user_id ON ingestion_job (user_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_job_status ON ingestion_job (status);

-- =============================================================================
-- 14. AUDIT LOG (Non-Repudiation & Traceability)
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES app_user(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log (action);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log (created_at);

-- =============================================================================
-- 15. ROW-LEVEL SECURITY (RLS) POLICIES
-- =============================================================================
ALTER TABLE app_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE sme ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE alternative_data_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE relationship ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_quality_flag ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_input_snapshot ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction ENABLE ROW LEVEL SECURITY;
ALTER TABLE explanation ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenario_result ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_job ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Service Role Policy (Full Access for Backend Service Key)
DROP POLICY IF EXISTS service_role_all ON app_user;
CREATE POLICY service_role_all ON app_user FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_sme ON sme;
CREATE POLICY service_role_sme ON sme FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_fin ON financial_record;
CREATE POLICY service_role_fin ON financial_record FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_alt ON alternative_data_record;
CREATE POLICY service_role_alt ON alternative_data_record FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_rel ON relationship;
CREATE POLICY service_role_rel ON relationship FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_dq ON data_quality_flag;
CREATE POLICY service_role_dq ON data_quality_flag FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_mr ON model_registry;
CREATE POLICY service_role_mr ON model_registry FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_ass ON assessment;
CREATE POLICY service_role_ass ON assessment FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_snap ON assessment_input_snapshot;
CREATE POLICY service_role_snap ON assessment_input_snapshot FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_pred ON prediction;
CREATE POLICY service_role_pred ON prediction FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_exp ON explanation;
CREATE POLICY service_role_exp ON explanation FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_scen ON scenario_result;
CREATE POLICY service_role_scen ON scenario_result FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_ing ON ingestion_job;
CREATE POLICY service_role_ing ON ingestion_job FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_aud ON audit_log;
CREATE POLICY service_role_aud ON audit_log FOR ALL TO service_role USING (true) WITH CHECK (true);
