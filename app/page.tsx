"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  ShieldCheck,
  Building2,
  TrendingUp,
  Share2,
  Lock,
  ArrowRight,
  SlidersHorizontal,
  FileCheck2,
} from "lucide-react";

export default function HomePage() {
  const { isAuthenticated, role, setRole } = useAuth();

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 space-y-12 text-[#16425b]">
      {/* Hero Section */}
      <div className="rounded-2xl bg-gradient-to-br from-[#16425b] via-[#2f6690] to-[#16425b] text-white p-8 sm:p-12 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 w-96 h-96 bg-[#81c3d7]/15 rounded-full blur-3xl pointer-events-none"></div>
        <div className="max-w-3xl space-y-4 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#81c3d7]/20 border border-[#81c3d7]/40 text-xs font-semibold uppercase tracking-wider text-[#81c3d7]">
            <ShieldCheck className="w-3.5 h-3.5" />
            Academic Prototype · Decision Support Only
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            RIPPLE — Explainable SME Credit-Risk Decision Support
          </h1>
          <p className="text-base sm:text-lg text-[#d9dcd6] leading-relaxed">
            Multi-modal decision intelligence combining 64-ratio tabular machine learning
            (Calibrated XGBoost), graph neural networks (GCN ego-network diffusion),
            local tabular SHAP attributions, and macroeconomic stress tests.
          </p>

          <div className="pt-4 flex flex-wrap gap-4">
            {!isAuthenticated ? (
              <>
                <Link
                  href="/login?returnUrl=%2Fbank"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#d9dcd6] hover:bg-white text-[#16425b] font-bold text-sm shadow-md transition"
                >
                  <Building2 className="w-4 h-4 text-[#2f6690]" />
                  Sign In as Bank Officer
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/login?returnUrl=%2Fsme"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#3a7ca5] hover:bg-[#16425b] border border-[#81c3d7]/40 text-white font-bold text-sm transition shadow-md"
                >
                  <ShieldCheck className="w-4 h-4 text-[#81c3d7]" />
                  Sign In as SME Borrower
                </Link>
              </>
            ) : role === "bank_officer" ? (
              <>
                <Link
                  href="/bank"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#d9dcd6] hover:bg-white text-[#16425b] font-bold text-sm shadow-md transition"
                >
                  <Building2 className="w-4 h-4 text-[#2f6690]" />
                  Portfolio Dashboard
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/bank/assess"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#3a7ca5] hover:bg-[#16425b] border border-[#81c3d7]/40 text-white font-bold text-sm transition shadow-md"
                >
                  <Building2 className="w-4 h-4 text-[#81c3d7]" />
                  Assessment Wizard
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/sme"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#d9dcd6] hover:bg-white text-[#16425b] font-bold text-sm shadow-md transition"
                >
                  <ShieldCheck className="w-4 h-4 text-[#2f6690]" />
                  Credit Readiness Dashboard
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/sme/upload"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#3a7ca5] hover:bg-[#16425b] border border-[#81c3d7]/40 text-white font-bold text-sm transition shadow-md"
                >
                  <ShieldCheck className="w-4 h-4 text-[#81c3d7]" />
                  Upload Statements
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Governance & Rule Safeguards (AGENTS.md) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-[#2f6690] font-bold text-sm">
            <Lock className="w-4 h-4 text-[#16425b]" />
            Rule 4.6: Decision Custody
          </div>
          <p className="text-xs text-[#2f6690] leading-relaxed font-medium">
            RIPPLE never automatically approves or rejects loans. The human bank officer retains sole decision authority; overrides are stored separately.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-[#2f6690] font-bold text-sm">
            <SlidersHorizontal className="w-4 h-4 text-[#16425b]" />
            Rule 4.7: SHAP Tabular Isolation
          </div>
          <p className="text-xs text-[#2f6690] leading-relaxed font-medium">
            SHAP applies strictly to the tabular model. Graph diffusion network signals are kept separate and never misattributed to SHAP.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-[#2f6690] font-bold text-sm">
            <Share2 className="w-4 h-4 text-[#16425b]" />
            Rule 4.4: Synthetic Relationship
          </div>
          <p className="text-xs text-[#2f6690] leading-relaxed font-medium">
            100% of generated commercial graph relationships are explicitly flagged as <code className="text-[11px] font-bold text-[#16425b] bg-[#d9dcd6] px-1 py-0.5 rounded">is_synthetic = true</code> across APIs and visualizers.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-[#2f6690] font-bold text-sm">
            <FileCheck2 className="w-4 h-4 text-[#16425b]" />
            Rule 4.8: Tenant Isolation
          </div>
          <p className="text-xs text-[#2f6690] leading-relaxed font-medium">
            SME borrowers receive credit readiness guidance. Internal bank PDs, internal committee comments, and raw model weights are strictly redacted.
          </p>
        </div>
      </div>

      {/* Core Workflow Modules */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-[#16425b]">
          Core Prototype Workflows
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="rounded-2xl p-6 bg-white/90 border border-[#3a7ca5]/30 shadow-xs flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-[#3a7ca5]/15 flex items-center justify-center text-[#2f6690]">
                <Building2 className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-base text-[#16425b]">
                Bank Portfolio Overview
              </h3>
              <p className="text-xs text-[#2f6690] leading-relaxed font-medium">
                Browse SME borrower accounts, review credit risk distributions, filter by sector, and inspect historical assessments and officer decisions.
              </p>
            </div>
            <Link
              href="/bank"
              onClick={() => setRole("bank_officer")}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2f6690] hover:text-[#16425b] transition"
            >
              Open Portfolio Dashboard <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Card 2 */}
          <div className="rounded-2xl p-6 bg-white/90 border border-[#3a7ca5]/30 shadow-xs flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-[#3a7ca5]/15 flex items-center justify-center text-[#2f6690]">
                <TrendingUp className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-base text-[#16425b]">
                Assessment Wizard
              </h3>
              <p className="text-xs text-[#2f6690] leading-relaxed font-medium">
                Input multi-year balance sheet and income statement line items or load presets (Healthy Tech, Distressed Manufacturing) to trigger end-to-end multi-modal scoring.
              </p>
            </div>
            <Link
              href="/bank/assess"
              onClick={() => setRole("bank_officer")}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2f6690] hover:text-[#16425b] transition"
            >
              Launch Assessment Wizard <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Card 3 */}
          <div className="rounded-2xl p-6 bg-white/90 border border-[#3a7ca5]/30 shadow-xs flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-[#3a7ca5]/15 flex items-center justify-center text-[#2f6690]">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-base text-[#16425b]">
                SME Credit Readiness
              </h3>
              <p className="text-xs text-[#2f6690] leading-relaxed font-medium">
                Empower SME owners with educational self-assessment guidance, document upload verification, and liquidity health indicators without exposing internal bank metrics.
              </p>
            </div>
            <Link
              href="/sme"
              onClick={() => setRole("sme_user")}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2f6690] hover:text-[#16425b] transition"
            >
              Visit SME Portal <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
