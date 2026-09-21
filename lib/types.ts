export type AppRole = "bank_officer" | "sme_user" | "admin";

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

export interface NetworkMetrics {
  is_cold_start: boolean;
  total_degree: number;
  in_degree: number;
  out_degree: number;
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

export interface SmeReadinessResponse {
  sme_id: string;
  business_name: string;
  readiness_status: "EVALUATED" | "PENDING_ASSESSMENT";
  is_complete?: boolean;
  credit_readiness_level?: "ADEQUATE" | "REQUIRES_ATTENTION";
  message?: string;
  guidance_tips: string[];
  disclaimer: string;
}
