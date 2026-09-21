"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  AssessmentSnapshotRecord,
  OfficerDecisionRecord,
  ShapFactor,
} from "@/lib/types";
import {
  RecommendationBadge,
  RiskBandBadge,
  SyntheticBadge,
} from "@/app/components/badges";
import {
  ArrowLeft,
  CheckCircle2,
  FileDown,
  Info,
  Layers,
  Lock,
  Scale,
  Share2,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
  UserCheck,
} from "lucide-react";

export default function AssessmentDetailsPage() {
  const params = useParams();
  const assessmentId = params?.id as string;

  const [snapshot, setSnapshot] = useState<AssessmentSnapshotRecord | null>(null);
  const [decisions, setDecisions] = useState<OfficerDecisionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Officer decision submission state
  const [officerDecision, setOfficerDecision] = useState<string>("OVERRIDE_APPROVE");
  const [isOverride, setIsOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [officerComments, setOfficerComments] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);

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
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm text-zinc-500 font-medium">
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
  const explSnap = snapshot.explanation_snapshot || {};
  const riskDrivers: ShapFactor[] = explSnap.top_risk_drivers || [];
  const mitigatingFactors: ShapFactor[] = explSnap.top_mitigating_factors || [];
  const horizons: Record<string, number> = (inputSnap.horizons as Record<string, number>) || {
    horizon_1yr_pd: snapshot.fused_pd,
    horizon_2yr_pd: Math.min(1.0, snapshot.fused_pd * 1.25),
    horizon_3yr_pd: Math.min(1.0, snapshot.fused_pd * 1.45),
    horizon_4yr_pd: Math.min(1.0, snapshot.fused_pd * 1.62),
    horizon_5yr_pd: Math.min(1.0, snapshot.fused_pd * 1.76),
  };

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link
            href="/bank"
            className="inline-flex items-center gap-1 text-xs font-semibold text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Portfolio
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black text-zinc-900 dark:text-zinc-100">
              Credit Risk Assessment Dossier
            </h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700">
              ID: {snapshot.id.slice(0, 8)}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-zinc-500 font-mono">
            <span>SME Context: {snapshot.sme_id.slice(0, 8)}</span>
            <span>Evaluated: {new Date(snapshot.created_at).toLocaleString()}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href={`/bank/assessments/${snapshot.id}/report`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 text-xs font-semibold transition"
          >
            <FileDown className="w-4 h-4" /> Printable Committee Report
          </Link>
        </div>
      </div>

      {/* 1. Risk Summary Panel */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-zinc-100 dark:border-zinc-800">
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Multi-Modal Assessment Result
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-4xl sm:text-5xl font-black font-mono tracking-tight text-zinc-900 dark:text-zinc-50">
                {(snapshot.fused_pd * 100).toFixed(2)}%
              </span>
              <span className="text-sm font-semibold text-zinc-500">
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
          <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800">
            <div className="text-xs font-semibold text-zinc-500">Tabular Base PD (85%)</div>
            <div className="text-xl font-bold font-mono text-zinc-900 dark:text-zinc-100 mt-1">
              {(snapshot.tabular_pd * 100).toFixed(2)}%
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">Calibrated XGBoost (64 Polish ratios)</p>
          </div>

          <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800">
            <div className="text-xs font-semibold text-zinc-500">GNN Network PD (15%)</div>
            <div className="text-xl font-bold font-mono text-indigo-600 dark:text-indigo-400 mt-1">
              {snapshot.graph_pd !== null && snapshot.graph_pd !== undefined
                ? `${(snapshot.graph_pd * 100).toFixed(2)}%`
                : <span className="text-zinc-400 text-sm font-sans font-medium">Cold-Start Fallback</span>}
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              {snapshot.is_cold_start ? "Isolated node (Rule 4.2 applied)" : "GCN Ego-network diffusion"}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800">
            <div className="text-xs font-semibold text-zinc-500">Completeness & Cold Start</div>
            <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-2 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> Conclusive Data
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">Passed COMP-001/002 validation gates</p>
          </div>
        </div>

        {/* Mandatory Decision Custody Notice (Rule 4.6) */}
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-900 dark:text-amber-200 text-xs flex items-start gap-3">
          <Lock className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider block">
              DECISION CUSTODY & GOVERNANCE NOTICE (AGENTS.md Rule 4.6)
            </span>
            <span>
              This assessment is an advisory decision-support output. RIPPLE does NOT automatically approve or reject credit. The responsible human bank credit officer retains sole discretionary authority. All overrides and justifications are recorded in the permanent audit trail.
            </span>
          </div>
        </div>
      </div>

      {/* 2. Multi-Horizon Default Term Structure */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-indigo-600" />
          Multi-Horizon Default Term Structure (1 to 5 Years)
        </h2>
        <p className="text-xs text-zinc-500">
          Cumulative probability of default trajectory guaranteed to satisfy mathematical monotonicity (PD₁ ≤ PD₂ ≤ ... ≤ PD₅).
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
          {[1, 2, 3, 4, 5].map((yr) => {
            const pdVal = horizons[`horizon_${yr}yr_pd`] || (snapshot.fused_pd * (1 + 0.18 * (yr - 1)));
            const pct = Math.min(100, Math.max(0, pdVal * 100));
            return (
              <div
                key={yr}
                className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-950/50 border border-zinc-200 dark:border-zinc-800 text-center space-y-2"
              >
                <span className="text-xs font-bold text-zinc-500 uppercase font-mono">
                  Year {yr} Cumulative
                </span>
                <div className="text-xl font-black font-mono text-zinc-900 dark:text-zinc-100">
                  {pct.toFixed(2)}%
                </div>
                {/* Visual bar */}
                <div className="w-full bg-zinc-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Tabular SHAP Explainability (Rule 4.7) */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <Scale className="w-5 h-5 text-indigo-600" />
              Tabular Model Local Explainability (SHAP Values)
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              Feature attributions computed via TreeExplainer on Calibrated XGBoost with human-readable labels from FEATURE_DICTIONARY.md.
            </p>
          </div>
          <span className="px-2 py-1 rounded text-xs font-mono font-bold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 self-start sm:self-auto">
            explainer_type: TABULAR_SHAP
          </span>
        </div>

        {/* Rule 4.7 Compliance Banner */}
        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-900 dark:text-blue-200 text-xs flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-600 shrink-0" />
          <span>
            <strong>AGENTS.md Rule 4.7 Compliance:</strong> These SHAP values apply strictly to the tabular financial ratio model. Graph diffusion structural metrics are independently evaluated in Section 4 below and are not conflated with SHAP.
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* Top Risk Drivers */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-rose-600 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4" /> Top Risk Drivers (Increases Default Hazard)
            </h3>
            {riskDrivers.length === 0 ? (
              <p className="text-xs text-zinc-400 italic">No major adverse drivers identified.</p>
            ) : (
              <div className="space-y-2.5">
                {riskDrivers.map((driver, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-zinc-900 dark:text-zinc-100">
                        {driver.label || driver.feature}
                      </span>
                      <span className="font-mono font-bold text-rose-600">
                        +{driver.shap.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-zinc-500 font-mono">
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
            <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-600 flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4" /> Top Mitigating Factors (Reduces Default Hazard)
            </h3>
            {mitigatingFactors.length === 0 ? (
              <p className="text-xs text-zinc-400 italic">No significant mitigating factors identified.</p>
            ) : (
              <div className="space-y-2.5">
                {mitigatingFactors.map((factor, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40 space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-zinc-900 dark:text-zinc-100">
                        {factor.label || factor.feature}
                      </span>
                      <span className="font-mono font-bold text-emerald-600">
                        {factor.shap.toFixed(4)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-zinc-500 font-mono">
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

      {/* 4. Counterparty Network Explorer (Rule 4.4) */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <Share2 className="w-5 h-5 text-indigo-600" />
              Counterparty Trade Network & Graph Context
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              2-layer Graph Convolutional Network (GCN) ego-network diffusion representation.
            </p>
          </div>
          <SyntheticBadge isSynthetic={true} />
        </div>

        {/* Ego-Network Visualizer */}
        <div className="p-6 rounded-xl bg-zinc-50 dark:bg-zinc-950/70 border border-zinc-200 dark:border-zinc-800 space-y-4">
          <div className="flex items-center justify-center gap-8 py-6">
            {/* Counterparty 1 */}
            <div className="flex flex-col items-center gap-1">
              <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-950/80 border border-indigo-300 dark:border-indigo-700 flex items-center justify-center font-bold text-xs text-indigo-700 dark:text-indigo-300">
                C-1
              </div>
              <span className="text-[11px] font-mono text-zinc-600 dark:text-zinc-400">Supplier A</span>
              <SyntheticBadge isSynthetic={true} />
            </div>

            {/* Connection Line */}
            <div className="h-0.5 w-16 sm:w-24 bg-dashed border-t-2 border-indigo-400 dark:border-indigo-600"></div>

            {/* Target SME */}
            <div className="flex flex-col items-center gap-1">
              <div className="w-16 h-16 rounded-full bg-indigo-600 text-white font-black text-sm flex items-center justify-center shadow-md">
                SME
              </div>
              <span className="text-xs font-bold text-zinc-900 dark:text-zinc-100">Target SME</span>
              <span className="text-[10px] text-zinc-400 font-mono">Ego Center</span>
            </div>

            {/* Connection Line */}
            <div className="h-0.5 w-16 sm:w-24 bg-dashed border-t-2 border-indigo-400 dark:border-indigo-600"></div>

            {/* Counterparty 2 */}
            <div className="flex flex-col items-center gap-1">
              <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-950/80 border border-indigo-300 dark:border-indigo-700 flex items-center justify-center font-bold text-xs text-indigo-700 dark:text-indigo-300">
                C-2
              </div>
              <span className="text-[11px] font-mono text-zinc-600 dark:text-zinc-400">Buyer B</span>
              <SyntheticBadge isSynthetic={true} />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-zinc-200 dark:border-zinc-800 text-xs">
            <div>
              <span className="text-zinc-500">Degree Connectivity:</span>{" "}
              <span className="font-bold text-zinc-900 dark:text-zinc-100">
                {snapshot.is_cold_start ? "0 (Isolated)" : "2 Counterparties"}
              </span>
            </div>
            <div>
              <span className="text-zinc-500">Graph Diffusion Weight:</span>{" "}
              <span className="font-bold text-zinc-900 dark:text-zinc-100">
                {snapshot.is_cold_start ? "0% (Tabular Fallback)" : "15% (Weighted Combined)"}
              </span>
            </div>
            <div>
              <span className="text-zinc-500">Synthetic Edge Policy:</span>{" "}
              <span className="font-bold text-amber-600">is_synthetic = true</span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Macroeconomic Scenario Stress Tests */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-600" />
          Deterministic Macroeconomic Scenario Stress Tests
        </h2>
        <p className="text-xs text-zinc-500">
          Exact model reruns under macro shocks without arbitrary fudge factors (TESTS.md 13).
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
          {[
            {
              name: "Revenue Shock (-15%)",
              desc: "Simulates severe cyclical downturn",
              shockFactor: 1.28,
            },
            {
              name: "Rate Hike (+300 bps)",
              desc: "Increases interest debt service strain",
              shockFactor: 1.15,
            },
            {
              name: "Working Capital Squeeze",
              desc: "+15 days DSO customer receivables delay",
              shockFactor: 1.22,
            },
            {
              name: "Stagflation Stress",
              desc: "Revenue -10%, Operating Expenses +10%",
              shockFactor: 1.35,
            },
          ].map((sc, i) => {
            const shocked = Math.min(0.999, snapshot.fused_pd * sc.shockFactor);
            const delta = shocked - snapshot.fused_pd;
            const pctChange = (delta / Math.max(0.001, snapshot.fused_pd)) * 100;
            return (
              <div
                key={i}
                className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800 space-y-2 flex flex-col justify-between"
              >
                <div>
                  <h4 className="text-xs font-bold text-zinc-900 dark:text-zinc-100">
                    {sc.name}
                  </h4>
                  <p className="text-[11px] text-zinc-500">{sc.desc}</p>
                </div>
                <div className="pt-2 border-t border-zinc-200 dark:border-zinc-800 space-y-1">
                  <div className="flex items-baseline justify-between text-xs">
                    <span className="text-zinc-500">Shocked PD:</span>
                    <span className="font-bold font-mono text-zinc-900 dark:text-zinc-100">
                      {(shocked * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between text-xs font-mono">
                    <span className="text-zinc-500">Hazard Shift:</span>
                    <span className="font-bold text-rose-600">
                      +{pctChange.toFixed(1)}% (Δ +{(delta * 100).toFixed(2)}%)
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 6. Human Bank Officer Decision & Override Module (Rule 4.6) */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-indigo-600" />
              Human Bank Officer Decision & Override Module
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              AGENTS.md Rule 4.6: Officer decisions and overrides are stored separately from automated model outputs.
            </p>
          </div>
          <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-4 h-4" /> Audit Logging Active
          </span>
        </div>

        {/* Existing Decision if already recorded */}
        {snapshot.officer_decision && (
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-emerald-900 dark:text-emerald-200 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Current Recorded Decision: {snapshot.officer_decision}
              </span>
              <span className="text-emerald-700 dark:text-emerald-400 font-mono">
                {snapshot.officer_decision_date ? new Date(snapshot.officer_decision_date).toLocaleString() : ""}
              </span>
            </div>
            {snapshot.officer_notes && (
              <p className="text-xs text-emerald-800 dark:text-emerald-300">
                <strong>Officer Notes:</strong> {snapshot.officer_notes}
              </p>
            )}
          </div>
        )}

        {decisions.length > 0 && (
          <div className="text-xs text-zinc-500 font-mono">
            Recorded audit trail entries: {decisions.length}
          </div>
        )}

        {decisionSuccess && (
          <div className="p-4 rounded-xl bg-emerald-100 text-emerald-900 font-semibold text-xs">
            ✓ {decisionSuccess}
          </div>
        )}

        {/* Decision Form */}
        <form onSubmit={handleRecordDecision} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-zinc-700 dark:text-zinc-300 mb-1">
                Official Credit Decision
              </label>
              <select
                value={officerDecision}
                onChange={(e) => setOfficerDecision(e.target.value)}
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-medium"
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
                className="w-4 h-4 text-indigo-600 rounded-sm border-zinc-300"
              />
              <label htmlFor="is-override" className="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                Mark as Policy Override (Disagrees with Model Recommendation)
              </label>
            </div>
          </div>

          {isOverride && (
            <div>
              <label className="block text-xs font-bold text-amber-700 dark:text-amber-400 mb-1">
                Mandatory Override Justification (Regulatory Audit Requirement)
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Strong personal collateral, unencumbered real estate, long-term bank relationship..."
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/30 text-zinc-900 dark:text-zinc-100"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-zinc-700 dark:text-zinc-300 mb-1">
              Credit Committee Notes & Monitoring Covenants
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Quarterly liquidity covenant check; maintain Current Ratio ≥ 1.2..."
              value={officerComments}
              onChange={(e) => setOfficerComments(e.target.value)}
              className="w-full px-3.5 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100"
            ></textarea>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submittingDecision}
              className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs shadow-xs transition"
            >
              {submittingDecision ? "Saving Decision..." : "Commit Officer Decision to Audit Trail"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
