"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { SmeReadinessResponse } from "@/lib/types";
import {
  ShieldCheck,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ArrowRight,
  RefreshCw,
  Lock,
  Info,
} from "lucide-react";

export default function SmePortalPage() {
  const [readiness, setReadiness] = useState<SmeReadinessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReadiness = () => {
    setLoading(true);
    setError(null);
    api
      .getSmeReadiness()
      .then((data) => setReadiness(data))
      .catch((err: unknown) => {
        console.error(err);
        const msg = err instanceof Error ? err.message : "Failed to load SME credit readiness summary.";
        setError(msg);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let active = true;
    api
      .getSmeReadiness()
      .then((data) => {
        if (active) setReadiness(data);
      })
      .catch((err: unknown) => {
        if (active) {
          console.error(err);
          const msg = err instanceof Error ? err.message : "Failed to load SME credit readiness summary.";
          setError(msg);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 text-xs font-semibold mb-2">
            <ShieldCheck className="w-3.5 h-3.5" /> SME Borrower Self-Assessment Portal
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-zinc-900 dark:text-zinc-100">
            Credit Readiness & Financial Health
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Confidential borrower dashboard for financial health monitoring and loan readiness guidance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchReadiness}
            className="p-2 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-850 text-zinc-600 dark:text-zinc-300 transition"
            title="Refresh readiness summary"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Link
            href="/sme/upload"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm shadow-xs transition"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Upload New Statements
          </Link>
        </div>
      </div>

      {/* AGENTS.md Rule 4.8 Compliance Banner */}
      <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 flex items-start gap-3">
        <Lock className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
        <div className="text-xs text-indigo-900 dark:text-indigo-200 space-y-1">
          <span className="font-bold uppercase tracking-wider block">
            PRIVACY & STRICT TENANT ISOLATION GUARANTEE (AGENTS.md Rule 4.8)
          </span>
          <p>
            Your business information is strictly isolated. This portal provides transparent self-readiness guidance. Internal bank credit officer comments, proprietary bank default scoring thresholds, and raw machine learning model parameters are completely private to the underwriting team and never exposed here.
          </p>
        </div>
      </div>

      {error ? (
        <div className="p-6 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300 space-y-1">
          <span className="font-bold">Error Loading Readiness:</span> {error}
        </div>
      ) : loading ? (
        <div className="p-16 text-center space-y-3">
          <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm text-zinc-500 font-medium">Evaluating financial statement readiness...</p>
        </div>
      ) : readiness ? (
        <div className="space-y-6">
          {/* Readiness Status Card */}
          <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-zinc-100 dark:border-zinc-800">
              <div className="space-y-1">
                <div className="text-xs font-semibold text-zinc-500 font-mono">
                  Registered Business
                </div>
                <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                  {readiness.business_name}
                </h2>
              </div>

              <div>
                {readiness.credit_readiness_level === "ADEQUATE" ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold uppercase bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Readiness: Adequate
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold uppercase bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Readiness: Requires Attention
                  </span>
                )}
              </div>
            </div>

            {/* Educational Actionable Tips */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-800 dark:text-zinc-200 flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-amber-500" />
                Key Financial Profile Guidance Tips
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {(readiness.guidance_tips || []).map((tip, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800 space-y-2"
                  >
                    <div className="w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 text-xs font-bold flex items-center justify-center">
                      {idx + 1}
                    </div>
                    <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed font-medium">
                      {tip}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Borrower Disclaimer */}
            <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-950/70 border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-zinc-700 dark:text-zinc-300">
                <Info className="w-3.5 h-3.5" /> Informational Guidance Notice
              </div>
              <p>{readiness.disclaimer}</p>
            </div>
          </div>

          {/* Document Upload Status Card */}
          <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                Keep Your Financial Profile Up to Date
              </h3>
              <p className="text-xs text-zinc-500">
                Uploading annual balance sheets and income statements helps maintain an accurate credit readiness evaluation.
              </p>
            </div>
            <Link
              href="/sme/upload"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition"
            >
              Upload Statements <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
