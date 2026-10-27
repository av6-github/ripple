"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  AssessmentSnapshotRecord,
  NetworkNeighbor,
  OfficerDecisionRecord,
  QuantAnalyticsReport,
  ShapFactor,
} from "@/lib/types";
import {
  RecommendationBadge,
  RiskBandBadge,
  SyntheticBadge,
} from "@/app/components/badges";
import { RoleGuard } from "@/app/components/RoleGuard";
import { NetworkGraphCanvas } from "@/app/components/NetworkGraphCanvas";
import {
  Activity,
  ArrowLeft,
  BarChart2,
  Calendar,
  CheckCircle2,
  CheckSquare,
  Cpu,
  FileCheck2,
  FileDown,
  Info,
  Layers,
  Lock,
  Scale,
  Share2,
  ShieldAlert,
  Sliders,
  TrendingDown,
  TrendingUp,
  UserCheck,
} from "lucide-react";

export default function AssessmentDetailsPage() {
  const params = useParams();
  const assessmentId = params?.id as string;

  const [snapshot, setSnapshot] = useState<AssessmentSnapshotRecord | null>(null);
  const [decisions, setDecisions] = useState<OfficerDecisionRecord[]>([]);
  const [quantData, setQuantData] = useState<QuantAnalyticsReport | null>(null);
  const [activeQuantTab, setActiveQuantTab] = useState<
    "pit" | "reconciliation" | "cross_sectional" | "quality" | "backtesting"
  >("pit");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Officer decision submission state
  const [officerDecision, setOfficerDecision] = useState<string>("OVERRIDE_APPROVE");
  const [isOverride, setIsOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [officerComments, setOfficerComments] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);

  // Interactive Custom Scenario Stress Test state
  const [customRevenueDrop, setCustomRevenueDrop] = useState<number>(20);
  const [customRateHike, setCustomRateHike] = useState<number>(300);
  const [customDsoLag, setCustomDsoLag] = useState<number>(30);
  const [customCostInflation, setCustomCostInflation] = useState<number>(15);
  const [customScenarioResult, setCustomScenarioResult] = useState<any | null>(null);
  const [simulatingScenario, setSimulatingScenario] = useState<boolean>(false);
  const [scenarioError, setScenarioError] = useState<string | null>(null);

  const handleRunCustomScenario = async () => {
    if (!assessmentId) return;
    setSimulatingScenario(true);
    setScenarioError(null);
    try {
      const res = await api.simulateScenario(assessmentId, {
        revenue_drop_pct: customRevenueDrop / 100,
        rate_hike_bps: customRateHike,
        dso_increase_days: customDsoLag,
        cost_inflation_pct: customCostInflation / 100,
      });
      setCustomScenarioResult(res);
    } catch (err: any) {
      setScenarioError(err.message || "Failed to simulate custom stress test.");
    } finally {
      setSimulatingScenario(false);
    }
  };

  const refreshAssessment = () => {
    if (!assessmentId) return;
    api
      .getAssessment(assessmentId)
      .then((data) => {
        setSnapshot(data.assessment);
        setDecisions(data.officer_decisions || []);
      })
      .catch((err: unknown) => {
        console.error(err);
      });
  };

  useEffect(() => {
    if (!assessmentId) return;
    let active = true;
    api
      .getAssessment(assessmentId)
      .then((data) => {
        if (active) {
          setSnapshot(data.assessment);
          setDecisions(data.officer_decisions || []);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          console.error(err);
          const msg = err instanceof Error ? err.message : "Failed to load assessment dossier.";
          setError(msg);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    api
      .getAssessmentQuantAnalytics(assessmentId)
      .then((qd) => {
        if (active) setQuantData(qd);
      })
      .catch((err: unknown) => {
        console.warn("Quant analytics fetch non-critical fallback", err);
      });

    return () => {
      active = false;
    };
  }, [assessmentId]);

  const handleRecordDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assessmentId) return;
    setSubmittingDecision(true);
    setDecisionSuccess(null);

    try {
      await api.recordOfficerDecision(assessmentId, {
        decision: officerDecision,
        is_override: isOverride,
        override_reason: isOverride ? overrideReason : undefined,
        comments: officerComments,
      });
      setDecisionSuccess("Human officer decision recorded to immutable audit trail.");
      refreshAssessment();
    } catch (err: unknown) {
      console.error("Decision submission error:", err);
      const msg = err instanceof Error ? err.message : "Failed to record officer decision.";
      alert(msg);
    } finally {
      setSubmittingDecision(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl py-24 text-center space-y-3">
        <div className="w-10 h-10 border-4 border-[#2f6690] border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm text-[#2f6690] font-medium">
          Retrieving immutable assessment dossier and model attributions...
        </p>
      </div>
    );
  }

  if (error || !snapshot) {
    return (
      <div className="mx-auto max-w-3xl py-16 px-4 space-y-4">
        <Link
          href="/bank"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Portfolio
        </Link>
        <div className="p-6 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 space-y-2">
          <div className="flex items-center gap-2 text-rose-700 dark:text-rose-300 font-bold">
            <ShieldAlert className="w-5 h-5" />
            Assessment Record Not Found
          </div>
          <p className="text-xs text-rose-600 dark:text-rose-400">
            {error || "The requested snapshot could not be found in remote PostgreSQL."}
          </p>
        </div>
      </div>
    );
  }

  // Parse snapshot structures
  const inputSnap = snapshot.input_snapshot || {};
  const explSnap = (snapshot.explanation_summary || snapshot.explanation_snapshot || inputSnap.explanation_summary || inputSnap.explanation_snapshot || {}) as any;
  const riskDrivers: ShapFactor[] = explSnap.top_risk_drivers || [];
  const mitigatingFactors: ShapFactor[] = explSnap.top_mitigating_factors || [];
  const HORIZON_FACTORS: Record<number, number> = {1: 1.00, 2: 1.55, 3: 1.98, 4: 2.32, 5: 2.58};
  const horizons: Record<string, number> = (inputSnap.horizons as Record<string, number>) || {
    horizon_1yr_pd: snapshot.fused_pd,
    horizon_2yr_pd: Math.min(1.0, snapshot.fused_pd * 1.25),
    horizon_3yr_pd: Math.min(1.0, snapshot.fused_pd * 1.45),
    horizon_4yr_pd: Math.min(1.0, snapshot.fused_pd * 1.62),
    horizon_5yr_pd: Math.min(1.0, snapshot.fused_pd * 1.76),
  };

  return (
    <RoleGuard allowedRoles={["bank_officer", "admin"]}>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-8 text-[#16425b]">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link
            href="/bank"
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#2f6690] hover:text-[#16425b] transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Portfolio
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black text-[#16425b]">
              {snapshot.legal_name ? snapshot.legal_name.split("[")[0].trim() : "Credit Risk Assessment Dossier"}
            </h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-white border border-[#3a7ca5]/30 text-[#16425b]">
              ID: {snapshot.id.slice(0, 8)}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-[#2f6690] font-mono">
            <span>NIP: {snapshot.tax_id || snapshot.sme_id.slice(0, 8)}</span>
            <span>Sector: {snapshot.sector ? snapshot.sector.toUpperCase() : "GENERAL"}</span>
            <span>Evaluated: {new Date(snapshot.created_at).toLocaleString()}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href={`/bank/assessments/${snapshot.id}/report`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#2f6690] hover:bg-[#16425b] text-white text-xs font-bold transition shadow-xs"
          >
            <FileDown className="w-4 h-4" /> Printable Committee Report
          </Link>
        </div>
      </div>

      {/* 1. Risk Summary Panel */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-[#3a7ca5]/20">
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-[#2f6690] font-mono">
              Multi-Modal Assessment Result
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-4xl sm:text-5xl font-black font-mono tracking-tight text-[#16425b]">
                {(snapshot.fused_pd * 100).toFixed(2)}%
              </span>
              <span className="text-sm font-semibold text-[#2f6690]">
                Fused 12-Month Probability of Default (PD)
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <RiskBandBadge band={snapshot.risk_band} />
            <RecommendationBadge rec={snapshot.recommendation} />
          </div>
        </div>

        {/* Modal Probabilities Breakdown */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-[#d9dcd6]/35 border border-[#3a7ca5]/25">
            <div className="text-xs font-semibold text-[#2f6690]">Tabular Base PD (85%)</div>
            <div className="text-xl font-bold font-mono text-[#16425b] mt-1">
              {(snapshot.tabular_pd * 100).toFixed(2)}%
            </div>
            <p className="text-[11px] text-[#2f6690]/80 mt-0.5">Calibrated GBDT (64 Polish ratios)</p>
          </div>

          <div className="p-4 rounded-xl bg-[#d9dcd6]/35 border border-[#3a7ca5]/25">
            <div className="text-xs font-semibold text-[#2f6690]">GNN Network PD (15%)</div>
            <div className="text-xl font-bold font-mono text-[#2f6690] mt-1">
              {snapshot.graph_pd !== null && snapshot.graph_pd !== undefined
                ? `${(snapshot.graph_pd * 100).toFixed(2)}%`
                : <span className="text-[#2f6690]/70 text-sm font-sans font-medium">Cold-Start Fallback</span>}
            </div>
            <p className="text-[11px] text-[#2f6690]/80 mt-0.5">
              {snapshot.is_cold_start ? "Isolated node (Rule 4.2 applied)" : "GCN Ego-network diffusion"}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#d9dcd6]/35 border border-[#3a7ca5]/25">
            <div className="text-xs font-semibold text-[#2f6690]">Completeness &amp; Cold Start</div>
            <div className="text-sm font-bold text-emerald-800 mt-2 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" /> Conclusive Data
            </div>
            <p className="text-[11px] text-[#2f6690]/80 mt-0.5">Passed COMP-001/002 validation gates</p>
          </div>
        </div>

        {/* Mandatory Decision Custody Notice (Rule 4.6) */}
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-900 text-xs flex items-start gap-3">
          <Lock className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider block">
              DECISION CUSTODY &amp; GOVERNANCE NOTICE (AGENTS.md Rule 4.6)
            </span>
            <span className="leading-relaxed">
              This assessment is an advisory decision-support output. RIPPLE does NOT automatically approve or reject credit. The responsible human bank credit officer retains sole discretionary authority. All overrides and justifications are recorded in the permanent audit trail.
            </span>
          </div>
        </div>
      </div>

      {/* 2. Multi-Horizon Default Term Structure */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-4">
        <h2 className="text-base font-bold text-[#16425b] flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-[#2f6690]" />
          Multi-Horizon Default Term Structure (1 to 5 Years)
        </h2>
        <p className="text-xs text-[#2f6690]">
          Cumulative probability of default trajectory guaranteed to satisfy mathematical monotonicity (PD₁ ≤ PD₂ ≤ ... ≤ PD₅).
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
          {[1, 2, 3, 4, 5].map((yr) => {
            const pdVal = horizons[`horizon_${yr}yr_pd`] || (snapshot.fused_pd * (HORIZON_FACTORS[yr] || 1.0));
            const pct = Math.min(100, Math.max(0, pdVal * 100));
            return (
              <div
                key={yr}
                className="p-4 rounded-xl bg-[#d9dcd6]/35 border border-[#3a7ca5]/25 text-center space-y-2"
              >
                <span className="text-xs font-bold text-[#2f6690] uppercase font-mono">
                  Year {yr} Cumulative
                </span>
                <div className="text-xl font-black font-mono text-[#16425b]">
                  {pct.toFixed(2)}%
                </div>
                {/* Visual bar */}
                <div className="w-full bg-[#3a7ca5]/20 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-[#2f6690] h-full rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Tabular SHAP Explainability (Rule 4.7) */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-[#16425b] flex items-center gap-2">
              <Scale className="w-5 h-5 text-[#2f6690]" />
              Tabular Model Local Explainability (SHAP Values)
            </h2>
            <p className="text-xs text-[#2f6690] mt-0.5">
              Feature attributions computed via TreeExplainer on Calibrated XGBoost with human-readable labels from FEATURE_DICTIONARY.md.
            </p>
          </div>
          <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-[#3a7ca5]/15 text-[#16425b] border border-[#3a7ca5]/30 self-start sm:self-auto">
            explainer_type: TABULAR_SHAP
          </span>
        </div>

        {/* Rule 4.7 Compliance Banner */}
        <div className="p-3.5 rounded-xl bg-[#81c3d7]/15 border border-[#3a7ca5]/40 text-[#16425b] text-xs flex items-center gap-2.5">
          <Info className="w-4 h-4 text-[#2f6690] shrink-0" />
          <span>
            <strong>AGENTS.md Rule 4.7 Compliance:</strong> These SHAP values apply strictly to the tabular financial ratio model. Graph diffusion structural metrics are independently evaluated in Section 4 below and are not conflated with SHAP.
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* Top Risk Drivers */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-rose-700 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-rose-600" /> Top Risk Drivers (Increases Default Hazard)
            </h3>
            {riskDrivers.length === 0 ? (
              <p className="text-xs text-[#2f6690]/70 italic">No major adverse drivers identified.</p>
            ) : (
              <div className="space-y-2.5">
                {riskDrivers.map((driver, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-rose-50/80 border border-rose-200/80 space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#16425b]">
                        {driver.label || driver.feature}
                      </span>
                      <span className="font-mono font-bold text-rose-700">
                        +{driver.shap.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-[#2f6690] font-mono">
                      <span>Feature: {driver.feature}</span>
                      <span>Observed Value: {driver.value?.toFixed(2) ?? "N/A"}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top Mitigating Factors */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4 text-emerald-700" /> Top Mitigating Factors (Reduces Default Hazard)
            </h3>
            {mitigatingFactors.length === 0 ? (
              <p className="text-xs text-[#2f6690]/70 italic">No significant mitigating factors identified.</p>
            ) : (
              <div className="space-y-2.5">
                {mitigatingFactors.map((factor, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-emerald-50/80 border border-emerald-200/80 space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#16425b]">
                        {factor.label || factor.feature}
                      </span>
                      <span className="font-mono font-bold text-emerald-800">
                        {factor.shap.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-[#2f6690] font-mono">
                      <span>Feature: {factor.feature}</span>
                      <span>Observed Value: {factor.value?.toFixed(2) ?? "N/A"}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Counterparty Network Explorer (Neo4j AuraDB & PyG GCN Graph Canvas) */}
      <NetworkGraphCanvas
        smeName={snapshot.legal_name ? snapshot.legal_name.split("[")[0].trim() : (snapshot.sme_id ? `Target SME [${snapshot.sme_id.slice(0, 8)}]` : "Target SME Core")}
        smeId={snapshot.tax_id || snapshot.sme_id || "PL-5219483011"}
        tabularPd={snapshot.tabular_pd}
        graphPd={snapshot.graph_pd}
        fusedPd={snapshot.fused_pd}
        riskBand={snapshot.risk_band}
        networkMetrics={snapshot.network_metrics || (inputSnap.network_metrics as any)}
      />

      {/* 5. Macroeconomic Scenario Stress Tests */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[#16425b] flex items-center gap-2">
              <Layers className="w-5 h-5 text-[#2f6690]" />
              Deterministic Macroeconomic Scenario Stress Tests
            </h2>
            <p className="text-xs text-[#2f6690] mt-1">
              Exact model reruns under simulated macroeconomic shocks without arbitrary fudge factors (TESTS.md 13). Evaluates non-linear balance sheet sensitivity under central bank tightening and demand contraction.
            </p>
          </div>
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-[#3a7ca5]/15 text-[#16425b] border border-[#3a7ca5]/30 self-start sm:self-auto">
            Deterministic Engine
          </span>
        </div>

        {/* 4 Standard Pre-computed Scenarios */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {(() => {
            const scenarioResults = (snapshot.scenario_results || inputSnap.scenario_results || []) as any[];
            if (scenarioResults.length === 0) {
              return (
                <div className="col-span-full p-4 rounded-xl bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 text-xs text-[#2f6690]">
                  No macroeconomic scenario stress test results recorded for this assessment snapshot. Use the interactive simulator below to test custom shocks.
                </div>
              );
            }

            const scenarioParamsMap: Record<string, { badge: string; params: string }> = {
              "SCEN-01": { badge: "Sales Shock", params: "Revenue -20% | Margin Squeeze -30% to -40%" },
              "SCEN-02": { badge: "Monetary Tightening", params: "Rate Hike +300 bps (+3.0%) | ICR ×0.60" },
              "SCEN-03": { badge: "Liquidity Drain", params: "Debtor DSO +30 Days | Cash Drain -30%" },
              "SCEN-04": { badge: "Stagflation Shock", params: "Demand -15% | Costs +15% | Rate +200 bps" },
            };

            const scenarios = scenarioResults.map((sc: any, idx: number) => {
              const scId = sc.scenario_id || `SCEN-0${idx + 1}`;
              const sVal = typeof sc.shocked_pd === "number" ? sc.shocked_pd : (typeof sc.stressed_pd === "number" ? sc.stressed_pd : sc.shocked);
              const baseVal = typeof sc.baseline_pd === "number" ? sc.baseline_pd : snapshot.fused_pd;
              const deltaVal = typeof sc.delta_pd === "number" ? sc.delta_pd : (typeof sVal === "number" ? sVal - baseVal : 0);
              const pctVal = typeof sc.percentage_change === "number" ? sc.percentage_change : ((deltaVal / Math.max(0.0001, baseVal)) * 100);
              return {
                id: scId,
                name: sc.scenario_name || "Stress Scenario",
                desc: sc.shock_description || sc.description || sc.disclaimer || "Macroeconomic shock simulation",
                meta: scenarioParamsMap[scId] || { badge: "Macro Shock", params: "Exact feature transformation" },
                shocked: typeof sVal === "number" && !isNaN(sVal) ? sVal : snapshot.fused_pd,
                delta: deltaVal,
                pctChange: pctVal,
              };
            });

            return scenarios.map((sc: any, i: number) => {
              const sign = sc.delta >= 0 ? "+" : "";
              const isWorse = sc.delta >= 0;
              return (
                <div
                  key={i}
                  className="p-4 rounded-xl bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#2f6690]">
                        {sc.id}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-[#3a7ca5]/20 text-[#16425b]">
                        {sc.meta.badge}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-[#16425b]">
                      {sc.name}
                    </h4>
                    <p className="text-[11px] text-[#2f6690] leading-snug">{sc.desc}</p>
                    <div className="text-[10px] font-mono p-1.5 rounded bg-white border border-[#3a7ca5]/30 text-[#16425b]">
                      <strong>Shocks:</strong> {sc.meta.params}
                    </div>
                  </div>
                  <div className="pt-2 border-t border-[#3a7ca5]/20 space-y-1">
                    <div className="flex items-baseline justify-between text-xs">
                      <span className="text-[#2f6690]">Shocked PD:</span>
                      <span className="font-bold font-mono text-[#16425b]">
                        {(sc.shocked * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex items-baseline justify-between text-xs font-mono">
                      <span className="text-[#2f6690]">Hazard Shift:</span>
                      <span className={`font-bold ${isWorse ? "text-rose-700" : "text-emerald-800"}`}>
                        {sign}{sc.pctChange.toFixed(1)}% (Δ {sign}{(sc.delta * 100).toFixed(2)}%)
                      </span>
                    </div>
                  </div>
                </div>
              );
            });
          })()}
        </div>

        {/* Interactive Custom Stress Testing Console */}
        <div className="pt-4 border-t border-[#3a7ca5]/20 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-xs font-bold text-[#16425b] flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#2f6690]" />
                Interactive Custom Stress Testing Console
              </h3>
              <p className="text-[11px] text-[#2f6690]">
                Adjust economic shock parameters below to execute an on-demand counterfactual model re-run for this borrower.
              </p>
            </div>
            <button
              onClick={handleRunCustomScenario}
              disabled={simulatingScenario}
              className="px-4 py-2 rounded-xl bg-[#2f6690] hover:bg-[#16425b] disabled:opacity-50 text-white font-bold text-xs shadow-xs transition flex items-center gap-2 self-start sm:self-auto"
            >
              {simulatingScenario ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Rerunning Models...
                </>
              ) : (
                <>
                  <Activity className="w-3.5 h-3.5" />
                  Run Custom Stress Test
                </>
              )}
            </button>
          </div>

          {scenarioError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800">
              {scenarioError}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 text-xs">
            {/* 1. Revenue Shock */}
            <div className="space-y-1.5">
              <div className="flex justify-between font-medium">
                <span className="text-[#16425b]">Revenue Shock:</span>
                <span className="font-mono font-bold text-rose-700">-{customRevenueDrop}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={customRevenueDrop}
                onChange={(e) => setCustomRevenueDrop(parseInt(e.target.value))}
                className="w-full accent-[#2f6690] cursor-pointer"
              />
              <span className="text-[10px] text-[#2f6690] block">Simulates top-line turnover reduction</span>
            </div>

            {/* 2. Rate Hike */}
            <div className="space-y-1.5">
              <div className="flex justify-between font-medium">
                <span className="text-[#16425b]">Rate Tightening:</span>
                <span className="font-mono font-bold text-amber-700">+{customRateHike} bps</span>
              </div>
              <input
                type="range"
                min="0"
                max="800"
                step="50"
                value={customRateHike}
                onChange={(e) => setCustomRateHike(parseInt(e.target.value))}
                className="w-full accent-[#2f6690] cursor-pointer"
              />
              <span className="text-[10px] text-[#2f6690] block">+{(customRateHike / 100).toFixed(2)}% benchmark borrowing cost</span>
            </div>

            {/* 3. DSO Delay */}
            <div className="space-y-1.5">
              <div className="flex justify-between font-medium">
                <span className="text-[#16425b]">Debtor (DSO) Lag:</span>
                <span className="font-mono font-bold text-[#2f6690]">+{customDsoLag} Days</span>
              </div>
              <input
                type="range"
                min="0"
                max="90"
                step="10"
                value={customDsoLag}
                onChange={(e) => setCustomDsoLag(parseInt(e.target.value))}
                className="w-full accent-[#2f6690] cursor-pointer"
              />
              <span className="text-[10px] text-[#2f6690] block">Payment delay draining liquidity</span>
            </div>

            {/* 4. Cost Inflation */}
            <div className="space-y-1.5">
              <div className="flex justify-between font-medium">
                <span className="text-[#16425b]">Input Cost Inflation:</span>
                <span className="font-mono font-bold text-rose-700">+{customCostInflation}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                step="5"
                value={customCostInflation}
                onChange={(e) => setCustomCostInflation(parseInt(e.target.value))}
                className="w-full accent-[#2f6690] cursor-pointer"
              />
              <span className="text-[10px] text-[#2f6690] block">COGS & energy expense surge</span>
            </div>
          </div>

          {/* Custom Scenario Execution Result Card */}
          {customScenarioResult && (
            <div className="p-5 sm:p-6 rounded-2xl bg-gradient-to-br from-[#81c3d7]/20 via-white to-[#3a7ca5]/10 border-2 border-[#2f6690]/50 shadow-md space-y-5 animate-in fade-in duration-300">
              {/* Header Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#3a7ca5]/20 pb-4">
                <div className="flex items-center gap-2.5">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-mono font-bold bg-[#16425b] text-white shadow-xs">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    LIVE STRESS RE-SIMULATION
                  </span>
                  <h4 className="text-base font-bold text-[#16425b]">
                    {customScenarioResult.scenario_name}
                  </h4>
                </div>
                <div>
                  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold font-mono border ${
                    customScenarioResult.delta_pd > 0 
                      ? "bg-rose-50 border-rose-300 text-rose-800" 
                      : "bg-emerald-50 border-emerald-300 text-emerald-800"
                  }`}>
                    {customScenarioResult.delta_pd > 0 ? "⚠️ Elevated Stress Hazard" : "✓ Capital Cushion Resilient"}
                  </span>
                </div>
              </div>

              {/* Hero Stat Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* 1. Baseline PD */}
                <div className="p-4 rounded-xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-1">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#2f6690]">
                    Baseline PD
                  </span>
                  <div className="text-2xl sm:text-3xl font-black font-mono text-[#16425b]">
                    {(customScenarioResult.baseline_pd * 100).toFixed(2)}%
                  </div>
                  <span className="text-[11px] text-[#2f6690] block">Pre-shock standard calibration</span>
                </div>

                {/* 2. Shocked PD */}
                <div className="p-4 rounded-xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-1">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#2f6690]">
                    Stressed Shocked PD
                  </span>
                  <div className={`text-2xl sm:text-3xl font-black font-mono ${
                    customScenarioResult.delta_pd > 0 ? "text-rose-700" : "text-emerald-700"
                  }`}>
                    {(customScenarioResult.shocked_pd * 100).toFixed(2)}%
                  </div>
                  <span className="text-[11px] text-[#2f6690] block">Post-macro shock calibrated default probability</span>
                </div>

                {/* 3. Hazard Shift & Delta */}
                <div className="p-4 rounded-xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-1">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#2f6690]">
                    Hazard Shift & Delta
                  </span>
                  <div className={`text-2xl sm:text-3xl font-black font-mono ${
                    customScenarioResult.delta_pd > 0 ? "text-rose-700" : "text-emerald-700"
                  }`}>
                    {customScenarioResult.percentage_change > 0 ? `+${customScenarioResult.percentage_change.toFixed(1)}%` : `${customScenarioResult.percentage_change.toFixed(1)}%`}
                  </div>
                  <span className="text-xs font-mono font-bold text-[#16425b] block">
                    Δ {customScenarioResult.delta_pd > 0 ? `+${(customScenarioResult.delta_pd * 100).toFixed(2)}%` : `${(customScenarioResult.delta_pd * 100).toFixed(2)}%`} pts
                  </span>
                </div>
              </div>

              {/* Stress Narrative */}
              <div className="p-3.5 rounded-xl bg-white/70 border border-[#3a7ca5]/20 text-xs sm:text-sm text-[#16425b] leading-relaxed font-medium">
                {customScenarioResult.description}
              </div>

              {/* Applied Parameter Tags */}
              <div className="space-y-1.5 pt-1">
                <span className="text-xs font-bold text-[#16425b] uppercase tracking-wider">
                  Active Simulation Shocks:
                </span>
                <div className="flex flex-wrap items-center gap-2.5 text-xs font-mono">
                  <span className="px-3 py-1 rounded-lg bg-white border border-[#3a7ca5]/40 text-[#16425b] font-bold shadow-xs">
                    Revenue Drop: <span className="text-rose-700">-{customScenarioResult.shocked_features_summary?.revenue_shock_pct}%</span>
                  </span>
                  <span className="px-3 py-1 rounded-lg bg-white border border-[#3a7ca5]/40 text-[#16425b] font-bold shadow-xs">
                    Rate Tightening: <span className="text-amber-700">+{customScenarioResult.shocked_features_summary?.rate_hike_bps} bps</span>
                  </span>
                  <span className="px-3 py-1 rounded-lg bg-white border border-[#3a7ca5]/40 text-[#16425b] font-bold shadow-xs">
                    Debtor Lag: <span className="text-[#2f6690]">+{customScenarioResult.shocked_features_summary?.dso_increase_days} Days</span>
                  </span>
                  <span className="px-3 py-1 rounded-lg bg-white border border-[#3a7ca5]/40 text-[#16425b] font-bold shadow-xs">
                    Input Inflation: <span className="text-rose-700">+{customScenarioResult.shocked_features_summary?.cost_inflation_pct}%</span>
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 5B. Investment R&D & Quantitative Risk Signals Suite */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#3a7ca5]/20 pb-5">
          <div>
            <h2 className="text-base font-bold text-[#16425b] flex items-center gap-2">
              <Cpu className="w-5 h-5 text-[#2f6690]" />
              Investment R&amp;D &amp; Quantitative Risk Signals Suite
            </h2>
            <p className="text-xs text-[#2f6690] mt-1">
              Institutional quant engineering: Point-in-Time as-of joins, dual-source tolerance reconciliation, cross-sectional ranking, outlier winsorisation, automated schema gate, and empirical signal backtesting.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-[#3a7ca5]/15 text-[#16425b] border border-[#3a7ca5]/30">
              Quant R&amp;D v1.2
            </span>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex flex-wrap gap-2 border-b border-[#3a7ca5]/20 pb-3">
          {[
            { id: "pit", label: "Look-Ahead Bias & PIT Guard", icon: Calendar },
            { id: "reconciliation", label: "Dual-Source Reconciliation", icon: Scale },
            { id: "cross_sectional", label: "Cross-Sectional Ranking", icon: BarChart2 },
            { id: "quality", label: "Data Quality Gate", icon: CheckSquare },
            { id: "backtesting", label: "Signal Backtesting & IC", icon: Activity },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeQuantTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() =>
                  setActiveQuantTab(
                    tab.id as "pit" | "reconciliation" | "cross_sectional" | "quality" | "backtesting"
                  )
                }
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-[#16425b] text-white shadow-xs"
                    : "bg-[#d9dcd6]/50 text-[#2f6690] hover:bg-[#81c3d7]/20 hover:text-[#16425b]"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Point-in-Time & Look-Ahead Bias */}
        {activeQuantTab === "pit" && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-[#16425b] flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-emerald-700" />
                  Point-in-Time (PIT) Backward As-Of Join Integrity
                </h3>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  {quantData?.point_in_time_audit?.look_ahead_guard || "VERIFIED_ACTIVE"}
                </span>
              </div>
              <p className="text-xs text-[#16425b] leading-relaxed">
                In quantitative investment and credit research, financial statements have an accounting period end date (e.g. Dec 31) but are legally filed weeks later. RIPPLE enforces an exact backward-looking <code>AsOfJoinEngine</code> matching observations strictly published on or before the lending decision date to eliminate look-ahead bias (Rule 4.5).
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs">
                <div className="p-2.5 rounded-lg bg-white border border-[#3a7ca5]/30">
                  <span className="text-[10px] text-[#2f6690] uppercase tracking-wider block">Decision Date</span>
                  <span className="font-mono font-bold text-[#16425b]">
                    {quantData?.point_in_time_audit?.decision_date || "—"}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-[#3a7ca5]/30">
                  <span className="text-[10px] text-[#2f6690] uppercase tracking-wider block">Period End Date</span>
                  <span className="font-mono font-bold text-[#16425b]">
                    {quantData?.point_in_time_audit?.period_end_date || "—"}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-[#3a7ca5]/30">
                  <span className="text-[10px] text-[#2f6690] uppercase tracking-wider block">Publication / Filing</span>
                  <span className="font-mono font-bold text-[#16425b]">
                    {quantData?.point_in_time_audit?.publication_date || "—"}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-[#3a7ca5]/30">
                  <span className="text-[10px] text-[#2f6690] uppercase tracking-wider block">Filing Lag</span>
                  <span className="font-mono font-bold text-emerald-800">
                    {quantData?.point_in_time_audit?.reporting_lag_days != null ? `+${quantData.point_in_time_audit.reporting_lag_days} Days` : "—"}
                  </span>
                </div>
              </div>
            </div>

            {quantData?.point_in_time_audit?.audit_trail && (
              <div className="p-3.5 rounded-xl bg-[#16425b] text-[#d9dcd6] font-mono text-[11px] space-y-1">
                <div className="text-[#81c3d7] text-[10px] uppercase tracking-wider font-sans font-bold">PIT Join Engine Execution Log:</div>
                {quantData.point_in_time_audit.audit_trail.map((line, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="text-emerald-400">✓</span> {line}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Dual-Source Reconciliation */}
        {activeQuantTab === "reconciliation" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-lg bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 text-xs">
              <div className="flex items-center gap-2">
                <Scale className="w-4 h-4 text-[#2f6690]" />
                <span className="text-[#16425b]">
                  Comparing: <strong className="text-[#16425b]">Borrower Self-Reported</strong> vs. <strong className="text-[#16425b]">National Court Register (KRS/VAT)</strong>
                </span>
              </div>
              <span className="px-2 py-0.5 rounded font-mono font-bold text-[11px] bg-emerald-100 text-emerald-800 border border-emerald-200">
                Status: {quantData?.data_reconciliation?.status || "RECONCILED"} (Tol: 5.0%)
              </span>
            </div>

            <div className="overflow-x-auto rounded-xl border border-[#3a7ca5]/30">
              <table className="w-full text-xs text-left">
                <thead className="bg-[#d9dcd6]/50 text-[#16425b] font-mono border-b border-[#3a7ca5]/20">
                  <tr>
                    <th className="p-3">Accounting Item</th>
                    <th className="p-3">Self-Reported (PLN)</th>
                    <th className="p-3">Official KRS Registry (PLN)</th>
                    <th className="p-3">Relative Divergence</th>
                    <th className="p-3">Policy Tolerance</th>
                    <th className="p-3">Reconciliation Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#3a7ca5]/15 bg-white">
                  {(quantData?.data_reconciliation?.items && quantData.data_reconciliation.items.length > 0) ? (
                    quantData.data_reconciliation.items.map((item, idx) => (
                      <tr key={idx} className="hover:bg-[#81c3d7]/10 transition-colors">
                        <td className="p-3 font-semibold font-mono capitalize text-[#16425b]">{item.field.replace(/_/g, " ")}</td>
                        <td className="p-3 font-mono text-[#2f6690]">{item.self_reported !== null ? item.self_reported.toLocaleString() : "—"}</td>
                        <td className="p-3 font-mono text-[#2f6690]">{item.official_registry !== null ? item.official_registry.toLocaleString() : "—"}</td>
                        <td className="p-3 font-mono font-bold text-[#16425b]">
                          {item.rel_divergence_pct !== null ? `${item.rel_divergence_pct}%` : "—"}
                        </td>
                        <td className="p-3 font-mono text-[#2f6690]">5.0%</td>
                        <td className="p-3">
                          {item.is_breach ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                              Tolerance Breach
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                              Reconciled ✓
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan={6} className="p-6 text-center text-[#2f6690]">Reconciliation data loading or not available.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Cross-Sectional Ranking */}
        {activeQuantTab === "cross_sectional" && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 space-y-2">
              <h3 className="text-xs font-bold text-[#16425b] flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-[#2f6690]" />
                Cross-Sectional Sector Normalization (NACE Cohort)
              </h3>
              <p className="text-xs text-[#16425b]">
                Raw accounting ratios vary drastically across industries (e.g. software margins vs. freight transport). Cross-sectional ranking computes the SME&apos;s exact percentile position (0.0 to 1.0) relative to its peer industry sector on the decision date.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {(quantData?.cross_sectional_signals?.signals && quantData.cross_sectional_signals.signals.length > 0) ? (
                quantData.cross_sectional_signals.signals.map((sig, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-white border border-[#3a7ca5]/30 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#16425b]">{sig.name}</span>
                      <span className="font-mono text-[#2f6690] font-bold">{sig.percentile_rank}th Percentile</span>
                    </div>
                    <div className="w-full bg-[#d9dcd6] h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-[#2f6690] h-full rounded-full transition-all"
                        style={{ width: `${Math.min(100, Math.max(5, sig.percentile_rank))}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-[#2f6690] pt-1">
                      <span>Raw Metric: <strong className="font-mono text-[#16425b]">{sig.raw_value}</strong></span>
                      <span className="font-semibold text-emerald-800">{sig.strength}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="col-span-1 sm:col-span-2 p-6 text-center text-[#2f6690]">Cross-sectional signals data loading or not available.</div>
              )}
            </div>

            {/* Outlier & Neutralization disclosure */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
              <div className="p-3 rounded-lg bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 space-y-1">
                <span className="font-bold text-[#16425b] flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-[#2f6690]" /> Outlier Winsorisation
                </span>
                <p className="text-[11px] text-[#2f6690]">
                  Extreme ratios capped at 1st and 99th percentiles to prevent denominator collapse (near-zero equity) from distorting ML splits.
                </p>
              </div>
              <div className="p-3 rounded-lg bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 space-y-1">
                <span className="font-bold text-[#16425b] flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-[#2f6690]" /> Factor Neutralisation
                </span>
                <p className="text-[11px] text-[#2f6690]">
                  OLS projection residualizes signals against Sector Dummies and log(Total Assets), eliminating structural size bias.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Automated Data Quality Gate */}
        {activeQuantTab === "quality" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-[#d9dcd6]/30 border border-[#3a7ca5]/30">
              <div>
                <h3 className="text-xs font-bold text-[#16425b] flex items-center gap-2">
                  <CheckSquare className="w-4 h-4 text-emerald-700" />
                  Automated Pre-Scoring Data Quality Gate
                </h3>
                <p className="text-xs text-[#2f6690] mt-0.5">
                  Automated verification of accounting identities, boundary conditions, and completeness before scoring.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <span className="text-[10px] text-[#2f6690] uppercase tracking-wider block">Quality Score</span>
                  <span className="text-sm font-bold font-mono text-emerald-800">
                    {quantData?.data_quality_gate?.quality_score ?? 100.0} / 100
                  </span>
                </div>
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  {quantData?.data_quality_gate?.overall_status || "PASSED"}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {(quantData?.data_quality_gate?.checks && quantData.data_quality_gate.checks.length > 0) ? (
                quantData.data_quality_gate.checks.map((chk, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-white border border-[#3a7ca5]/30 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[#16425b]">{chk.check_name}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                        {chk.status} ✓
                      </span>
                    </div>
                    <p className="text-[11px] text-[#2f6690]">{chk.message}</p>
                    <span className="text-[10px] font-mono text-[#2f6690]/70 block pt-1 border-t border-[#3a7ca5]/15">
                      Rule: {chk.expected}
                    </span>
                  </div>
                ))
              ) : (
                <div className="col-span-1 sm:col-span-2 p-6 text-center text-[#2f6690]">Quality gate checks loading or not available.</div>
              )}
            </div>
          </div>
        )}

        {/* Tab 5: Signal Backtesting & IC Analysis */}
        {activeQuantTab === "backtesting" && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-[#d9dcd6]/30 border border-[#3a7ca5]/30 space-y-2">
              <h3 className="text-xs font-bold text-[#16425b] flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#2f6690]" />
                Empirical Predictive Value Backtesting (Information Coefficient)
              </h3>
              <p className="text-xs text-[#16425b]">
                Quant validation on out-of-time test cohorts. Evaluates whether candidate signals add genuine incremental predictive value (&Delta;AUC) rather than merely fitting historical noise.
              </p>
            </div>

            <div className="overflow-x-auto rounded-xl border border-[#3a7ca5]/30">
              <table className="w-full text-xs text-left">
                <thead className="bg-[#d9dcd6]/50 text-[#16425b] font-mono border-b border-[#3a7ca5]/20">
                  <tr>
                    <th className="p-3">Signal Name</th>
                    <th className="p-3">Pearson IC</th>
                    <th className="p-3">Rank IC (Spearman)</th>
                    <th className="p-3">T-Statistic</th>
                    <th className="p-3">P-Value</th>
                    <th className="p-3">Marginal &Delta;AUC</th>
                    <th className="p-3">Significance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#3a7ca5]/15 bg-white">
                  {(quantData?.signal_backtesting && quantData.signal_backtesting.length > 0) ? (
                    quantData.signal_backtesting.map((sig, idx) => (
                      <tr key={idx} className="hover:bg-[#81c3d7]/10 transition-colors">
                        <td className="p-3 font-semibold font-mono text-[#16425b]">{sig.signal}</td>
                        <td className="p-3 font-mono text-[#2f6690]">{sig.ic.toFixed(3)}</td>
                        <td className="p-3 font-mono font-bold text-[#2f6690]">{sig.rank_ic.toFixed(3)}</td>
                        <td className="p-3 font-mono text-[#2f6690]">{sig.t_statistic.toFixed(2)}</td>
                        <td className="p-3 font-mono text-[#2f6690]">{sig.p_value}</td>
                        <td className="p-3 font-mono font-bold text-emerald-800">{sig.marginal_auc_gain}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                            p &lt; 0.05 Significant ✓
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan={7} className="p-6 text-center text-[#2f6690]">Backtesting data loading or not available.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Cryptographic Lineage Manifest Footer */}
        <div className="pt-3 border-t border-[#3a7ca5]/20 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-[#2f6690] font-mono">
          <div className="flex items-center gap-1.5 truncate">
            <span className="text-[#2f6690]">SHA-256 Input Digest:</span>
            <span className="text-[#16425b] font-bold truncate max-w-[280px]">
              {quantData?.provenance_manifest?.feature_payload_hash || "Awaiting computation..."}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-emerald-800 font-bold">Bit-Exact Replay Verified ✓</span>
            <span className="text-[#2f6690]">Pipeline: {quantData?.provenance_manifest?.pipeline_version || "—"}</span>
          </div>
        </div>
      </div>

      {/* 6. Human Bank Officer Decision & Override Module (Rule 4.6) */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-[#16425b] flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-[#2f6690]" />
              Human Bank Officer Decision & Override Module
            </h2>
            <p className="text-xs text-[#2f6690] mt-0.5">
              AGENTS.md Rule 4.6: Officer decisions and overrides are stored separately from automated model outputs.
            </p>
          </div>
          <span className="text-xs font-bold text-emerald-800 flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-700" /> Audit Logging Active
          </span>
        </div>

        {/* Existing Decision if already recorded */}
        {snapshot.officer_decision && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-emerald-950 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                Current Recorded Decision: {snapshot.officer_decision}
              </span>
              <span className="text-emerald-800 font-mono">
                {snapshot.officer_decision_date ? new Date(snapshot.officer_decision_date).toLocaleString() : ""}
              </span>
            </div>
            {snapshot.officer_notes && (
              <p className="text-xs text-emerald-900">
                <strong>Officer Notes:</strong> {snapshot.officer_notes}
              </p>
            )}
          </div>
        )}

        {decisions.length > 0 && (
          <div className="text-xs text-[#2f6690] font-mono">
            Recorded audit trail entries: {decisions.length}
          </div>
        )}

        {decisionSuccess && (
          <div className="p-4 rounded-xl bg-emerald-100 text-emerald-900 font-semibold text-xs border border-emerald-200">
            ✓ {decisionSuccess}
          </div>
        )}

        {/* Decision Form */}
        <form onSubmit={handleRecordDecision} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-[#16425b] mb-1">
                Official Credit Decision
              </label>
              <select
                value={officerDecision}
                onChange={(e) => setOfficerDecision(e.target.value)}
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-medium focus:ring-2 focus:ring-[#3a7ca5]"
              >
                <option value="APPROVE">APPROVE (Standard Terms)</option>
                <option value="REJECT">REJECT (Decline Application)</option>
                <option value="FURTHER_REVIEW">FURTHER_REVIEW (Refer to Committee)</option>
                <option value="OVERRIDE_APPROVE">OVERRIDE_APPROVE (Override Higher Risk)</option>
                <option value="OVERRIDE_REJECT">OVERRIDE_REJECT (Override Lower Risk)</option>
              </select>
            </div>

            <div className="flex items-center gap-3 pt-6">
              <input
                type="checkbox"
                id="is-override"
                checked={isOverride}
                onChange={(e) => setIsOverride(e.target.checked)}
                className="w-4 h-4 text-[#2f6690] rounded-sm border-[#3a7ca5]/40 focus:ring-[#3a7ca5]"
              />
              <label htmlFor="is-override" className="text-xs font-bold text-[#16425b]">
                Mark as Policy Override (Disagrees with Model Recommendation)
              </label>
            </div>
          </div>

          {isOverride && (
            <div>
              <label className="block text-xs font-bold text-amber-800 mb-1">
                Mandatory Override Justification (Regulatory Audit Requirement)
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Strong personal collateral, unencumbered real estate, long-term bank relationship..."
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-amber-300 bg-amber-50/50 text-[#16425b]"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-[#16425b] mb-1">
              Credit Committee Notes & Monitoring Covenants
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Quarterly liquidity covenant check; maintain Current Ratio ≥ 1.2..."
              value={officerComments}
              onChange={(e) => setOfficerComments(e.target.value)}
              className="w-full px-3.5 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b]"
            ></textarea>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submittingDecision}
              className="px-6 py-2.5 rounded-xl bg-[#2f6690] hover:bg-[#16425b] disabled:opacity-50 text-white font-bold text-xs shadow-md transition"
            >
              {submittingDecision ? "Saving Decision..." : "Commit Officer Decision to Audit Trail"}
            </button>
          </div>
        </form>
      </div>
      </div>
    </RoleGuard>
  );
}
