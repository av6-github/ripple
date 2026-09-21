"""Credit risk assessment orchestration service for RIPPLE.

Implements end-to-end assessment pipeline:
- Completeness gating
- Feature calculation
- Tabular & GNN prediction
- Fusion & risk banding
- Tabular SHAP explanations
- Scenario stress testing
- Multi-horizon curves
- Recommendation generation
- Immutable snapshot persistence
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from backend.domain.enums import Confidence, SourceType
from backend.domain.schemas import FinancialStatementData
from backend.features.domain import AlternativeDataInput, FinancialStatementPeriod
from backend.features.feature_engine import FeatureEngine
from backend.fusion.recommendation import RecommendationType
from backend.repositories.assessment_repository import AssessmentRepository
from backend.services.completeness_service import CompletenessEvaluator
from backend.services.ml_client import MLClient


class AssessmentService:
    """Orchestrates comprehensive SME credit risk assessments."""

    def __init__(
        self,
        assessment_repo: Optional[AssessmentRepository] = None,
        ml_client: Optional[MLClient] = None,
    ) -> None:
        self.repo = assessment_repo or AssessmentRepository()
        self.ml = ml_client or MLClient()
        self.feature_engine = FeatureEngine()
        self.completeness_evaluator = CompletenessEvaluator()

    def run_assessment(
        self,
        sme_id: str,
        statement_periods: List[FinancialStatementPeriod],
        alt_data: Optional[AlternativeDataInput] = None,
        officer_id: Optional[str] = None,
        network_neighbors: Optional[List[str]] = None,
        network_edges: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """Execute full credit risk assessment for an SME."""
        # Verify SME exists
        sme = self.repo.get_sme_by_id(sme_id)
        if not sme:
            raise ValueError(f"SME with ID '{sme_id}' not found.")

        # 1. Evaluate Data Completeness
        latest_period = statement_periods[-1]
        stmt_data = FinancialStatementData(
            revenue=latest_period.total_revenue,
            total_assets=latest_period.total_assets,
            total_liabilities=latest_period.total_liabilities,
            equity=latest_period.total_equity,
            current_assets=latest_period.current_assets,
            short_term_liabilities=latest_period.short_term_liabilities,
            net_profit=latest_period.net_profit,
            ebit=latest_period.operating_profit_ebit,
            cash_and_equivalents=latest_period.cash_and_equivalents,
            source_type=SourceType.EXTRACTED_FILE,
            source_ref=f"sme_{sme_id}_statement_{latest_period.fiscal_year or 'latest'}",
            confidence=Confidence.VERIFIED,
        )
        completeness = self.completeness_evaluator.evaluate(stmt_data)

        # 2. Extract Features
        feature_res = self.feature_engine.extract_from_statements(statement_periods, alt_data=alt_data)
        features = feature_res.features
        flags = feature_res.flags
        indicators = feature_res.indicators

        # 3. Check Completeness Gate (COMP-001, COMP-002, AGENTS.md Rule 4.2)
        if not completeness.is_conclusive or completeness.completeness_score_pct < 60.0:
            rec = self.ml.generate_recommendation(
                fused_pd=None,
                completeness_score=completeness.completeness_score_pct / 100.0,
                critical_field_missing=True,
                data_quality_flags=flags,
            )
            snapshot = self.repo.create_assessment_snapshot(
                sme_id=sme_id,
                officer_id=officer_id,
                tabular_pd=0.0,
                graph_pd=None,
                fused_pd=0.0,
                calibrated_pd=0.0,
                risk_band="INCONCLUSIVE",
                recommendation=RecommendationType.INCONCLUSIVE.value,
                is_inconclusive=True,
                is_cold_start=True,
                explanation_summary={"status": "INCONCLUSIVE", "missing_fields": completeness.missing_critical_fields},
                scenario_results=[],
                network_metrics={},
            )
            return {
                "assessment_id": snapshot["id"],
                "sme_id": sme_id,
                "status": "INCONCLUSIVE",
                "completeness": completeness.completeness_score_pct,
                "recommendation": RecommendationType.INCONCLUSIVE.value,
                "rationale": rec.rationale,
                "missing_critical_fields": completeness.missing_critical_fields,
            }

        # 4. Transform Features for Model Pipeline (dim 67)
        feature_df = pd.DataFrame([features])
        X_proc = self.ml.preprocessor.transform(feature_df)

        # 5. Predict Tabular PD
        tabular_pd = self.ml.predict_tabular_pd(X_proc)

        # 6. Network Risk Assessment (or Cold-Start Fallback)
        net_assessment = self.ml.assess_network(
            business_id=sme_id,
            neighbor_ids=network_neighbors,
            network_edges=network_edges,
        )

        # 7. Multi-Modal Fusion & Risk Banding
        fused = self.ml.fuse_risks(
            business_id=sme_id,
            tabular_pd=tabular_pd,
            graph_pd=net_assessment.graph_pd,
            is_cold_start=net_assessment.is_cold_start,
        )

        # 8. SHAP Explainability (strictly tabular features)
        net_signals = {
            "is_cold_start": net_assessment.is_cold_start,
            "total_degree": net_assessment.total_degree,
            "in_degree": net_assessment.in_degree,
            "out_degree": net_assessment.out_degree,
        }
        explanation = self.ml.explain_tabular(X_proc, network_influence=net_signals)

        # 9. Multi-Horizon Projections
        horizons = self.ml.project_horizons(fused.fused_pd)

        # 10. Scenario Stress Testing
        scenarios = self.ml.run_scenarios(X_proc, baseline_pd=fused.fused_pd)
        scenario_dicts = [
            {
                "scenario_id": s.scenario_id,
                "scenario_name": s.scenario_name,
                "baseline_pd": s.baseline_pd,
                "shocked_pd": s.shocked_pd,
                "delta_pd": s.delta_pd,
                "percentage_change": s.percentage_change,
                "disclaimer": s.disclaimer,
            }
            for s in scenarios
        ]

        # 11. Decision Recommendation
        concerns = [d.display_label for d in explanation.top_risk_drivers[:3]]
        strengths = [m.display_label for m in explanation.top_mitigating_factors[:3]]
        rec = self.ml.generate_recommendation(
            fused_pd=fused.fused_pd,
            completeness_score=completeness.completeness_score_pct / 100.0,
            critical_field_missing=False,
            negative_equity=flags.get("negative_equity_flag", False),
            data_quality_flags=flags,
            top_concerns=concerns,
            top_strengths=strengths,
        )

        # 12. Persist Snapshot to Remote PostgreSQL
        explanation_summary = {
            "explainer_type": explanation.explainer_type,
            "top_risk_drivers": [
                {"label": d.display_label, "feature": d.feature_name, "value": d.feature_value, "shap": d.shap_value}
                for d in explanation.top_risk_drivers
            ],
            "top_mitigating_factors": [
                {"label": m.display_label, "feature": m.feature_name, "value": m.feature_value, "shap": m.shap_value}
                for m in explanation.top_mitigating_factors
            ],
        }

        snapshot = self.repo.create_assessment_snapshot(
            sme_id=sme_id,
            officer_id=officer_id,
            tabular_pd=fused.tabular_pd,
            graph_pd=fused.graph_pd,
            fused_pd=fused.fused_pd,
            calibrated_pd=fused.fused_pd,
            risk_band=fused.risk_band.value,
            recommendation=rec.recommendation.value,
            is_inconclusive=False,
            is_cold_start=fused.is_cold_start,
            explanation_summary=explanation_summary,
            scenario_results=scenario_dicts,
            network_metrics=net_signals,
        )

        return {
            "assessment_id": snapshot["id"],
            "sme_id": sme_id,
            "tabular_pd": fused.tabular_pd,
            "graph_pd": fused.graph_pd,
            "fused_pd": fused.fused_pd,
            "risk_band": fused.risk_band.value,
            "recommendation": rec.recommendation.value,
            "rationale": rec.rationale,
            "decision_custody_notice": rec.decision_authority_notice,
            "is_cold_start": fused.is_cold_start,
            "fusion_mode": fused.fusion_mode,
            "explanation": explanation_summary,
            "network_metrics": net_signals,
            "multi_horizon_pd": horizons,
            "scenario_stress_tests": scenario_dicts,
            "indicators": indicators,
            "created_at": str(snapshot["created_at"]),
        }
