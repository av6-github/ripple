export type AppRole = "bank_officer" | "sme_user" | "admin";

export interface AuthUser {
  id: string;
  email: string;
  role: AppRole;
  first_name?: string | null;
  last_name?: string | null;
  organization?: string | null;
  sme_id?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role: AppRole;
  first_name?: string;
  last_name?: string;
  organization?: string;
  tax_id?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export type RiskBand =
  | "Band A (Low Risk)"
  | "Band B (Moderate Risk)"
  | "Band C (Elevated Risk)"
  | "Band D (High Risk)"
  | "INCONCLUSIVE"
  | "LOW"
  | "MEDIUM_LOW"
  | "MEDIUM"
  | "MEDIUM_HIGH"
  | "HIGH"
  | "VERY_HIGH";

export type Recommendation =
  | "LOWER_RISK"
  | "FURTHER_REVIEW"
  | "HIGHER_RISK"
  | "INCONCLUSIVE";

export interface SmeProfile {
  id: string;
  legal_name: string;
  tax_id: string;
  industry?: string;
  sector?: string;
  is_synthetic?: boolean;
  country?: string;
  currency?: string;
  created_at: string;
}

export interface StatementPeriod {
  fiscal_year: number;
  total_assets: number;
  current_assets: number;
  cash_and_equivalents: number;
  inventory?: number;
  accounts_receivable?: number;
  total_liabilities: number;
  short_term_liabilities: number;
  total_equity: number;
  total_revenue: number;
  cost_of_goods_sold?: number;
  gross_profit?: number;
  operating_profit_ebit: number;
  net_profit: number;
  operating_cash_flow?: number;
  interest_expense?: number;
}

export interface ShapFactor {
  label: string;
  feature: string;
  value: number;
  shap: number;
}

export interface ShapExplanationSummary {
  explainer_type: "TABULAR_SHAP" | string;
  top_risk_drivers: ShapFactor[];
  top_mitigating_factors: ShapFactor[];
}

export interface ScenarioResult {
  scenario_id: string;
  scenario_name: string;
  baseline_pd: number;
  shocked_pd: number;
  delta_pd: number;
  percentage_change: number;
  disclaimer: string;
}

export interface NetworkNeighbor {
  id: string;
  name: string;
  type: string;
  role?: string;
  direction: "incoming" | "outgoing" | "bidirectional" | string;
  annual_volume?: number;
  tenure_months?: number;
  risk_level?: string;
}

export interface NetworkMetrics {
  is_cold_start: boolean;
  total_degree: number;
  in_degree: number;
  out_degree: number;
  neighbors?: NetworkNeighbor[];
  edges?: number[][];
}

export interface AssessmentResponse {
  assessment_id: string;
  sme_id: string;
  tabular_pd: number;
  graph_pd: number | null;
  fused_pd: number;
  risk_band: RiskBand;
  recommendation: Recommendation;
  rationale: string;
  decision_custody_notice: string;
  is_cold_start: boolean;
  fusion_mode: string;
  explanation: ShapExplanationSummary;
  network_metrics: NetworkMetrics;
  multi_horizon_pd: Record<string, number>;
  scenario_stress_tests: ScenarioResult[];
  indicators: Record<string, boolean>;
  created_at: string;
}

export interface AssessmentSnapshotRecord {
  id: string;
  sme_id: string;
  officer_id: string;
  status: string;
  input_snapshot: Record<string, unknown>;
  explanation_snapshot: ShapExplanationSummary;
  is_inconclusive: boolean;
  is_cold_start: boolean;
  officer_decision?: string;
  officer_notes?: string;
  officer_decision_date?: string;
  created_at: string;
  tabular_pd: number;
  graph_pd: number | null;
  fused_pd: number;
  calibrated_pd: number;
  risk_band: RiskBand;
  recommendation: Recommendation;
  network_metrics?: NetworkMetrics;
  scenario_results?: ScenarioResult[];
  explanation_summary?: ShapExplanationSummary;
  model_version?: string;
  legal_name?: string;
  tax_id?: string;
  sector?: string;
  industry?: string;
  city?: string;
}

export interface OfficerDecisionRecord {
  id: string;
  assessment_id: string;
  officer_id: string;
  decision: "APPROVE" | "REJECT" | "FURTHER_REVIEW" | "OVERRIDE_APPROVE" | "OVERRIDE_REJECT";
  is_override: boolean;
  override_reason?: string;
  comments?: string;
  decided_at?: string;
}

export interface SmeCompanyProfile {
  legal_name: string;
  tax_id: string;
  regon: string;
  sector: string;
  industry: string;
  city: string;
  incorporation_date: string;
  verification_status: string;
}

export interface SmeFinancialSnapshot {
  fiscal_year: number;
  total_revenue: number;
  cost_of_goods_sold: number;
  gross_profit: number;
  operating_profit: number;
  net_profit: number;
  total_assets: number;
  current_assets: number;
  cash_and_equivalents: number;
  accounts_receivable: number;
  inventory: number;
  total_liabilities: number;
  short_term_liabilities: number;
  total_equity: number;
  working_capital: number;
}

export interface SmeOperationalMetrics {
  current_ratio: number;
  cash_ratio: number;
  equity_ratio_pct: number;
  dso_days: number;
  dpo_days: number;
  dio_days: number;
  cash_conversion_cycle_days: number;
  working_capital_runway_months: number;
  working_capital_fragility_velocity: number;
}

export interface SmeNetworkSummary {
  active_counterparties_count: number;
  average_receivable_lag_days: number;
  commercial_relationship_stability: string;
  is_synthetic_graph: boolean;
}

export interface SmeStatementHistoryItem {
  fiscal_year: number;
  revenue: number;
  operating_profit: number;
  net_profit: number;
  total_assets: number;
  status: string;
}

export interface SmeReadinessResponse {
  sme_id: string;
  business_name: string;
  readiness_status: "EVALUATED" | "PENDING_ASSESSMENT";
  is_complete?: boolean;
  credit_readiness_level?: "ADEQUATE" | "REQUIRES_ATTENTION";
  message?: string;
  guidance_tips: string[];
  disclaimer: string;
  company_profile?: SmeCompanyProfile;
  financial_snapshot?: SmeFinancialSnapshot;
  operational_metrics?: SmeOperationalMetrics;
  commercial_network_summary?: SmeNetworkSummary;
  statement_history?: SmeStatementHistoryItem[];
}

export interface QuantReconciliationRow {
  field: string;
  self_reported: number | null;
  official_registry: number | null;
  abs_diff: number | null;
  rel_divergence_pct: number | null;
  is_breach: boolean;
  note: string;
}

export interface CrossSectionalSignalItem {
  name: string;
  raw_value: string | number;
  percentile_rank: number;
  interpretation: string;
  strength: string;
}

export interface SignalBacktestRow {
  signal: string;
  ic: number;
  rank_ic: number;
  t_statistic: number;
  p_value: string;
  marginal_auc_gain: string;
  enhanced_auc: number;
  is_significant: boolean;
  direction: string;
}

export interface QuantAnalyticsReport {
  assessment_id: string;
  sme_name: string;
  point_in_time_audit: {
    is_point_in_time_compliant: boolean;
    decision_date: string;
    period_end_date: string;
    publication_date: string;
    reporting_lag_days: number;
    decision_lag_days: number;
    look_ahead_guard: string;
    audit_trail: string[];
    methodology: string;
  };
  data_reconciliation: {
    status: "RECONCILED" | "TOLERANCE_BREACH" | "UNRECONCILED" | "SOURCE_MISSING";
    source_a: string;
    source_b: string;
    tolerance_threshold_pct: number;
    max_divergence_pct: number;
    breached_count: number;
    items: QuantReconciliationRow[];
    audit_notes: string[];
  };
  cross_sectional_signals: {
    peer_cohort_sector: string;
    peer_sample_size: number;
    signals: CrossSectionalSignalItem[];
  };
  outlier_and_neutralization: {
    winsorisation: {
      lower_percentile_cutoff: string;
      upper_percentile_cutoff: string;
      status: string;
      benefit: string;
    };
    neutralization: {
      methodology: string;
      controlled_factors: string[];
      residual_correlation_with_size: number;
      status: string;
      benefit: string;
    };
  };
  data_quality_gate: {
    overall_status: "PASSED" | "WARNING" | "FAILED";
    quality_score: number;
    passed_checks: number;
    warning_checks: number;
    failed_checks: number;
    checks: Array<{
      check_name: string;
      category: string;
      status: string;
      message: string;
      expected: string;
    }>;
  };
  signal_backtesting: SignalBacktestRow[];
  provenance_manifest: {
    feature_payload_hash: string;
    model_version: string;
    model_artifact_hash: string;
    pipeline_version: string;
    as_of_timestamp: string;
    reproducibility_signature: string;
    is_replay_verified: boolean;
  };
}

export interface IngestionJobResult {
  job_id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  status: string;
  financial_data?: {
    fiscal_year?: number | null;
    revenue?: number | null;
    operating_expenses?: number | null;
    ebit?: number | null;
    ebitda?: number | null;
    net_profit?: number | null;
    total_assets?: number | null;
    current_assets?: number | null;
    cash_and_equivalents?: number | null;
    receivables?: number | null;
    inventory?: number | null;
    fixed_assets?: number | null;
    total_liabilities?: number | null;
    short_term_liabilities?: number | null;
    long_term_liabilities?: number | null;
    equity?: number | null;
    working_capital?: number | null;
    source_type?: string;
    source_ref?: string;
    confidence?: string;
  };
  extraction_confidence?: Record<string, string>;
  quality_flags?: Array<{
    field_name: string;
    flag_type: string;
    severity: string;
    message: string;
  }>;
  completeness?: {
    completeness_score_pct: number;
    is_conclusive: boolean;
    missing_critical_fields: string[];
    missing_optional_fields: string[];
    inconclusive_reason?: string | null;
  };
  error_message?: string | null;
}

export interface LoanApplicationRecord {
  id: string;
  sme_id: string;
  facility_type: string;
  requested_amount: number;
  tenor_months: number;
  purpose: string;
  self_reported_revenue: number;
  self_reported_assets: number;
  self_reported_liabilities: number;
  self_reported_equity: number;
  self_reported_net_profit: number;
  self_reported_cash: number;
  contact_name?: string | null;
  contact_email?: string | null;
  status: "PENDING_REVIEW" | "ASSESSED" | "APPROVED" | "REJECTED" | string;
  assessment_id?: string | null;
  created_at: string;
  updated_at: string;
  legal_name?: string;
  tax_id?: string;
  sector?: string;
  industry?: string;
  city?: string;
}

export interface CreateLoanApplicationRequest {
  sme_id?: string;
  facility_type: string;
  requested_amount: number;
  tenor_months: number;
  purpose: string;
  self_reported_revenue: number;
  self_reported_assets: number;
  self_reported_liabilities: number;
  self_reported_equity: number;
  self_reported_net_profit: number;
  self_reported_cash: number;
  contact_name?: string;
  contact_email?: string;
}

