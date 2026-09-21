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
  const { setRole } = useAuth();

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 space-y-12">
      {/* Hero Section */}
      <div className="rounded-2xl bg-gradient-to-br from-indigo-900 via-indigo-800 to-slate-900 text-white p-8 sm:p-12 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="max-w-3xl space-y-4 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/30 border border-indigo-400/40 text-xs font-semibold uppercase tracking-wider text-indigo-200">
            <ShieldCheck className="w-3.5 h-3.5" />
            Academic Prototype · Decision Support Only
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            RIPPLE — Explainable SME Credit-Risk Decision Support
          </h1>
          <p className="text-base sm:text-lg text-indigo-100/90 leading-relaxed">
            Multi-modal decision intelligence combining 64-ratio tabular machine learning
            (Calibrated XGBoost), graph neural networks (GCN ego-network diffusion),
            local tabular SHAP attributions, and macroeconomic stress tests.
          </p>

          <div className="pt-4 flex flex-wrap gap-4">
            <Link
              href="/bank"
              onClick={() => setRole("bank_officer")}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-white text-indigo-950 font-bold text-sm shadow-md hover:bg-indigo-50 transition"
            >
              <Building2 className="w-4 h-4 text-indigo-600" />
              Bank Officer Portal
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/sme"
              onClick={() => setRole("sme_user")}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-indigo-700/80 hover:bg-indigo-700 border border-indigo-500/50 text-white font-bold text-sm transition"
            >
              <ShieldCheck className="w-4 h-4 text-emerald-300" />
              SME Credit Readiness
            </Link>
          </div>
        </div>
      </div>

      {/* Governance & Rule Safeguards (AGENTS.md) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-sm">
            <Lock className="w-4 h-4" />
            Rule 4.6: Decision Custody
          </div>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            RIPPLE never automatically approves or rejects loans. The human bank officer retains sole decision authority; overrides are stored separately.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-bold text-sm">
            <SlidersHorizontal className="w-4 h-4" />
            Rule 4.7: SHAP Tabular Isolation
          </div>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            SHAP applies strictly to the tabular model. Graph diffusion network signals are kept separate and never misattributed to SHAP.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-bold text-sm">
            <Share2 className="w-4 h-4" />
            Rule 4.4: Synthetic Relationship
          </div>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            100% of generated commercial graph relationships are explicitly flagged as <code className="text-[11px] font-bold text-amber-600">is_synthetic = true</code> across APIs and visualizers.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-sm">
            <FileCheck2 className="w-4 h-4" />
            Rule 4.8: Tenant Isolation
          </div>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            SME borrowers receive credit readiness guidance. Internal bank PDs, internal committee comments, and raw model weights are strictly redacted.
          </p>
        </div>
      </div>

      {/* Core Workflow Modules */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Core Prototype Workflows
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="rounded-xl p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-950/60 flex items-center justify-center text-indigo-600">
                <Building2 className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-base text-zinc-900 dark:text-zinc-100">
                Bank Portfolio Overview
              </h3>
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Browse SME borrower accounts, review credit risk distributions, filter by sector, and inspect historical assessments and officer decisions.
              </p>
            </div>
            <Link
              href="/bank"
              onClick={() => setRole("bank_officer")}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
            >
              Open Portfolio Dashboard <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Card 2 */}
          <div className="rounded-xl p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600">
                <TrendingUp className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-base text-zinc-900 dark:text-zinc-100">
                Assessment Wizard
              </h3>
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Input multi-year balance sheet and income statement line items or load presets (Healthy Tech, Distressed Manufacturing) to trigger end-to-end multi-modal scoring.
              </p>
            </div>
            <Link
              href="/bank/assess"
              onClick={() => setRole("bank_officer")}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
            >
              Launch Assessment Wizard <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Card 3 */}
          <div className="rounded-xl p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-950/60 flex items-center justify-center text-purple-600">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-base text-zinc-900 dark:text-zinc-100">
                SME Credit Readiness
              </h3>
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Empower SME owners with educational self-assessment guidance, document upload verification, and liquidity health indicators without exposing internal bank metrics.
              </p>
            </div>
            <Link
              href="/sme"
              onClick={() => setRole("sme_user")}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-purple-600 hover:text-purple-700 dark:text-purple-400"
            >
              Visit SME Portal <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
