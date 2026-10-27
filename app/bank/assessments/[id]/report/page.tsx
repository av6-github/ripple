"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { AssessmentSnapshotRecord, ShapFactor } from "@/lib/types";
import {
  RecommendationBadge,
  RiskBandBadge,
} from "@/app/components/badges";
import { RoleGuard } from "@/app/components/RoleGuard";
import { ArrowLeft, Printer } from "lucide-react";

export default function AssessmentReportPage() {
  const params = useParams();
  const assessmentId = params?.id as string;

  const [snapshot, setSnapshot] = useState<AssessmentSnapshotRecord | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!assessmentId) return;
    let active = true;
    api
      .getAssessment(assessmentId)
      .then((data) => {
        if (active) setSnapshot(data.assessment);
      })
      .catch((err: unknown) => {
        console.error(err);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [assessmentId]);

  if (loading || !snapshot) {
    return (
      <div className="py-20 text-center text-sm text-zinc-500 font-medium">
        Loading assessment report...
      </div>
    );
  }

  const explSnap =
    snapshot.explanation_summary || snapshot.explanation_snapshot || {};
  const riskDrivers = explSnap.top_risk_drivers || [];
  const mitigatingFactors = explSnap.top_mitigating_factors || [];

  return (
    <RoleGuard allowedRoles={["bank_officer", "admin"]}>
      <div className="mx-auto max-w-4xl px-6 py-10 space-y-8 bg-white text-zinc-900 min-h-screen">
      {/* Non-print controls */}
      <div className="print:hidden flex items-center justify-between pb-4 border-b border-zinc-200">
        <Link
          href={`/bank/assessments/${snapshot.id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-600 hover:text-zinc-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Assessment Dossier
        </Link>
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#2f6690] text-white font-bold text-xs shadow-sm hover:bg-[#16425b] transition"
        >
          <Printer className="w-4 h-4" /> Print / Save as PDF
        </button>
      </div>

      {/* Memorandum Header */}
      <div className="border-b-2 border-zinc-900 pb-6 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-widest text-[#2f6690]">
            RIPPLE Academic Decision Support Platform
          </span>
          <span className="text-xs font-mono text-zinc-500">
            CONFIDENTIAL · BANK CREDIT COMMITTEE
          </span>
        </div>
        <h1 className="text-2xl font-black tracking-tight text-zinc-950">
          CREDIT RISK ASSESSMENT MEMORANDUM
        </h1>
        <div className="grid grid-cols-2 text-xs font-mono pt-2 text-zinc-600">
          <div>Assessment Snapshot ID: {snapshot.id}</div>
          <div>Evaluation Timestamp: {new Date(snapshot.created_at).toLocaleString()}</div>
          <div>Borrower SME ID: {snapshot.sme_id}</div>
          <div>Model Bundle: {snapshot?.model_version || "v1.0.0 (XGBoost Calibrated + GCN)"}</div>
        </div>
      </div>

      {/* Executive Risk Summary */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-900 border-b border-zinc-200 pb-1">
          1. Multi-Modal Default Risk Summary
        </h2>
        <div className="grid grid-cols-3 gap-4 p-4 rounded-lg bg-zinc-50 border border-zinc-200 text-center">
          <div>
            <div className="text-[11px] text-zinc-500 font-semibold">Fused 12-Month PD</div>
            <div className="text-2xl font-black font-mono mt-1 text-zinc-900">
              {(snapshot.fused_pd * 100).toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-[11px] text-zinc-500 font-semibold">Basel Standard Risk Band</div>
            <div className="mt-1">
              <RiskBandBadge band={snapshot.risk_band} />
            </div>
          </div>
          <div>
            <div className="text-[11px] text-zinc-500 font-semibold">System Recommendation</div>
            <div className="mt-1">
              <RecommendationBadge rec={snapshot.recommendation} />
            </div>
          </div>
        </div>
        <div className="text-xs text-zinc-600 space-y-1">
          <p>
            <strong>Tabular Model Base Probability of Default:</strong> {(snapshot.tabular_pd * 100).toFixed(2)}%
          </p>
          <p>
            <strong>GNN Counterparty Network Default Signal:</strong>{" "}
            {snapshot.graph_pd !== null && snapshot.graph_pd !== undefined
              ? `${(snapshot.graph_pd * 100).toFixed(2)}%`
              : "Cold-Start Isolated Node Fallback (AGENTS.md Rule 4.2 applied)"}
          </p>
        </div>
      </div>

      {/* Explanatory Attribution Summary (Rule 4.7) */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-900 border-b border-zinc-200 pb-1">
          2. Tabular Feature Attributions (SHAP)
        </h2>
        <p className="text-[11px] text-zinc-500 italic">
          Attributions derived via TreeExplainer on Calibrated XGBoost. GNN network signals are kept distinct and not conflated with SHAP (AGENTS.md Rule 4.7).
        </p>
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <h3 className="font-bold text-rose-700 mb-2">Primary Risk Drivers:</h3>
            <ul className="space-y-1.5 font-mono text-[11px]">
              {riskDrivers.map((d: ShapFactor, idx: number) => (
                <li key={idx} className="p-2 bg-rose-50 border border-rose-100 rounded">
                  <span className="font-bold text-zinc-900">{d.label || d.feature}</span>: +{d.shap.toFixed(4)} (Observed: {d.value?.toFixed(2) ?? "N/A"})
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-bold text-emerald-700 mb-2">Primary Mitigating Factors:</h3>
            <ul className="space-y-1.5 font-mono text-[11px]">
              {mitigatingFactors.map((m: ShapFactor, idx: number) => (
                <li key={idx} className="p-2 bg-emerald-50 border border-emerald-100 rounded">
                  <span className="font-bold text-zinc-900">{m.label || m.feature}</span>: {m.shap.toFixed(4)} (Observed: {m.value?.toFixed(2) ?? "N/A"})
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Human Officer Decision & Custody Statement (Rule 4.6) */}
      <div className="space-y-3 pt-4 border-t-2 border-zinc-900">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-900 border-b border-zinc-200 pb-1">
          3. Bank Officer Decision Record & Sign-Off (Rule 4.6)
        </h2>
        <div className="p-4 rounded-lg bg-zinc-50 border border-zinc-200 space-y-3 text-xs">
          <div className="flex items-center justify-between">
            <span><strong>Recorded Decision:</strong> {snapshot.officer_decision || "PENDING_OFFICER_REVIEW"}</span>
            <span><strong>Decision Date:</strong> {snapshot.officer_decision_date ? new Date(snapshot.officer_decision_date).toLocaleDateString() : "Pending"}</span>
          </div>
          {snapshot.officer_notes && (
            <p><strong>Committee Notes / Covenants:</strong> {snapshot.officer_notes}</p>
          )}
          <p className="text-[11px] text-zinc-500 italic">
            Governance Certification: The bank credit officer retains sole discretionary authority over loan approval or rejection. RIPPLE model recommendations serve exclusively as decision-support guidance.
          </p>
          <div className="pt-8 flex justify-between text-xs font-mono">
            <div className="border-t border-zinc-400 w-48 text-center pt-1">Credit Risk Officer Signature</div>
            <div className="border-t border-zinc-400 w-48 text-center pt-1">Senior Underwriter Signature</div>
          </div>
        </div>
      </div>
      </div>
    </RoleGuard>
  );
}
