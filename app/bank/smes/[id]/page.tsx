"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { AssessmentSnapshotRecord, SmeProfile } from "@/lib/types";
import {
  RecommendationBadge,
  RiskBandBadge,
  SyntheticBadge,
} from "@/app/components/badges";
import { RoleGuard } from "@/app/components/RoleGuard";
import {
  Building2,
  Calendar,
  CreditCard,
  FileText,
  PlusCircle,
  ArrowLeft,
  ArrowRight,
  ShieldAlert,
  Clock,
  AlertTriangle,
} from "lucide-react";

export default function SmeProfilePage() {
  const params = useParams();
  const smeId = params?.id as string;

  const [sme, setSme] = useState<SmeProfile | null>(null);
  const [assessments, setAssessments] = useState<AssessmentSnapshotRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!smeId) return;

    let active = true;
    api
      .getSmeProfile(smeId)
      .then((data) => {
        if (active) {
          setSme(data.sme);
          setAssessments(data.assessments);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          console.error(err);
          const msg = err instanceof Error ? err.message : "Failed to load SME profile.";
          setError(msg);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [smeId]);

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl py-20 text-center space-y-3">
        <div className="w-8 h-8 border-4 border-[#2f6690] border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm text-[#2f6690] font-medium">Loading SME profile and records...</p>
      </div>
    );
  }

  if (error || !sme) {
    return (
      <div className="mx-auto max-w-3xl py-16 px-4 space-y-4 text-[#16425b]">
        <Link
          href="/bank"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2f6690] hover:text-[#16425b] transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Portfolio
        </Link>
        <div className="p-6 rounded-2xl bg-rose-50 border border-rose-300 space-y-2 shadow-xs">
          <div className="flex items-center gap-2 text-rose-800 font-bold">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            Error Loading SME Profile
          </div>
          <p className="text-xs text-rose-700">
            {error || "SME record not found in remote repository."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <RoleGuard allowedRoles={["bank_officer", "admin"]}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8 space-y-8 text-[#16425b]">
      {/* Back Link */}
      <Link
        href="/bank"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2f6690] hover:text-[#16425b] transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Portfolio
      </Link>

      {/* SME Header Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black text-[#16425b]">
              {sme.legal_name}
            </h1>
            {sme.is_synthetic && <SyntheticBadge isSynthetic={true} />}
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs text-[#2f6690] font-mono">
            <span className="flex items-center gap-1">
              <CreditCard className="w-3.5 h-3.5 text-[#3a7ca5]" /> Tax ID: {sme.tax_id}
            </span>
            <span className="flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5 text-[#3a7ca5]" /> Sector: {sme.sector || sme.industry || "General"}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-[#3a7ca5]" /> Enrolled: {new Date(sme.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        <div>
          <Link
            href={`/bank/assess?sme_id=${sme.id}`}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2f6690] hover:bg-[#16425b] text-white font-bold text-sm shadow-md transition"
          >
            <PlusCircle className="w-4 h-4" />
            Run New Assessment
          </Link>
        </div>
      </div>

      {/* Historical Assessments */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-[#16425b] flex items-center gap-2">
            <Clock className="w-5 h-5 text-[#2f6690]" />
            Historical Credit Assessments ({assessments.length})
          </h2>
          <span className="text-xs text-[#2f6690] font-mono">
            Immutable Audit Trail (Rule 4.6)
          </span>
        </div>

        {assessments.length === 0 ? (
          <div className="p-10 text-center rounded-2xl border border-[#3a7ca5]/30 bg-white/90 space-y-3 shadow-xs">
            <FileText className="w-8 h-8 text-[#2f6690]/60 mx-auto" />
            <h3 className="text-sm font-bold text-[#16425b]">
              No Previous Assessments Recorded
            </h3>
            <p className="text-xs text-[#2f6690] max-w-sm mx-auto">
              This SME has not yet undergone multi-modal risk scoring. Click below to launch the assessment wizard.
            </p>
            <Link
              href={`/bank/assess?sme_id=${sme.id}`}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#2f6690] hover:bg-[#16425b] text-white text-xs font-bold shadow-md transition"
            >
              <PlusCircle className="w-3.5 h-3.5" /> Start First Assessment
            </Link>
          </div>
        ) : (
          <div className="rounded-2xl border border-[#3a7ca5]/30 bg-white/90 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-[#3a7ca5]/30 bg-[#3a7ca5]/10 text-xs font-bold uppercase tracking-wider text-[#16425b]">
                  <tr>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Tabular PD</th>
                    <th className="py-3 px-4">Graph PD</th>
                    <th className="py-3 px-4">Fused PD</th>
                    <th className="py-3 px-4">Risk Band</th>
                    <th className="py-3 px-4">System Recommendation</th>
                    <th className="py-3 px-4">Officer Decision</th>
                    <th className="py-3 px-4 text-right">Snapshot</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#3a7ca5]/20">
                  {assessments.map((snap) => (
                    <tr
                      key={snap.id}
                      className="hover:bg-[#81c3d7]/15 transition"
                    >
                      <td className="py-3.5 px-4 text-xs font-mono text-[#2f6690]">
                        {new Date(snap.created_at).toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-[#16425b]">
                        {(snap.tabular_pd * 100).toFixed(2)}%
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs">
                        {snap.graph_pd !== null && snap.graph_pd !== undefined
                          ? `${(snap.graph_pd * 100).toFixed(2)}%`
                          : <span className="text-[#2f6690]/60 italic">Cold-Start</span>}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs font-bold text-[#16425b]">
                        {(snap.fused_pd * 100).toFixed(2)}%
                      </td>
                      <td className="py-3.5 px-4">
                        <RiskBandBadge band={snap.risk_band} />
                      </td>
                      <td className="py-3.5 px-4">
                        <RecommendationBadge rec={snap.recommendation} />
                      </td>
                      <td className="py-3.5 px-4">
                        {snap.officer_decision ? (
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold font-mono ${
                              snap.officer_decision.includes("APPROVE")
                                ? "bg-emerald-100 text-emerald-800"
                                : snap.officer_decision.includes("REJECT")
                                ? "bg-rose-100 text-rose-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {snap.officer_decision}
                          </span>
                        ) : (
                          <span className="text-xs text-amber-800 font-semibold flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3 text-amber-600" /> Pending Decision
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/bank/assessments/${snap.id}`}
                          className="inline-flex items-center gap-1 text-xs font-bold text-[#2f6690] hover:text-[#16425b]"
                        >
                          View Snapshot <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
      </div>
    </RoleGuard>
  );
}
