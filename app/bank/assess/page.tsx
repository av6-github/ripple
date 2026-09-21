"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { SmeProfile, StatementPeriod } from "@/lib/types";
import {
  Activity,
  ArrowLeft,
  Building2,
  Sparkles,
  AlertCircle,
  FileSpreadsheet,
  Share2,
} from "lucide-react";

// Wrap in Suspense to satisfy Next.js useSearchParams client component requirement
export default function AssessmentWizardPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-4xl py-20 text-center">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm text-zinc-500 mt-2 font-medium">Loading wizard...</p>
        </div>
      }
    >
      <AssessmentWizardContent />
    </Suspense>
  );
}

function AssessmentWizardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialSmeId = searchParams.get("sme_id") || "";

  const [smes, setSmes] = useState<SmeProfile[]>([]);
  const [selectedSmeId, setSelectedSmeId] = useState<string>(initialSmeId);
  const [loadingSmes, setLoadingSmes] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Network context options
  const [includeNetwork, setIncludeNetwork] = useState(true);

  // Financial line items state (latest annual statement)
  const [formData, setFormData] = useState({
    fiscal_year: 2023,
    total_assets: 650000,
    current_assets: 280000,
    cash_and_equivalents: 75000,
    inventory: 45000,
    accounts_receivable: 95000,
    total_liabilities: 250000,
    short_term_liabilities: 140000,
    total_equity: 400000,
    total_revenue: 800000,
    cost_of_goods_sold: 450000,
    gross_profit: 350000,
    operating_profit_ebit: 110000,
    net_profit: 75000,
    operating_cash_flow: 95000,
    interest_expense: 15000,
  });

  useEffect(() => {
    api
      .listSmes()
      .then((data) => {
        setSmes(data);
        if (!selectedSmeId && data.length > 0) {
          setSelectedSmeId(data[0].id);
        }
      })
      .catch((err) => console.error("Error fetching SMEs:", err))
      .finally(() => setLoadingSmes(false));
  }, [selectedSmeId]);

  const handleInputChange = (field: string, val: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: field === "fiscal_year" ? parseInt(val) || 2023 : parseFloat(val) || 0,
    }));
  };

  // Demo presets
  const applyPreset = (presetType: "healthy" | "distressed" | "incomplete") => {
    if (presetType === "healthy") {
      setFormData({
        fiscal_year: 2023,
        total_assets: 900000,
        current_assets: 450000,
        cash_and_equivalents: 150000,
        inventory: 60000,
        accounts_receivable: 120000,
        total_liabilities: 250000,
        short_term_liabilities: 120000,
        total_equity: 650000,
        total_revenue: 1200000,
        cost_of_goods_sold: 650000,
        gross_profit: 550000,
        operating_profit_ebit: 220000,
        net_profit: 160000,
        operating_cash_flow: 190000,
        interest_expense: 10000,
      });
      setIncludeNetwork(true);
    } else if (presetType === "distressed") {
      setFormData({
        fiscal_year: 2023,
        total_assets: 500000,
        current_assets: 120000,
        cash_and_equivalents: 8000,
        inventory: 85000,
        accounts_receivable: 40000,
        total_liabilities: 490000,
        short_term_liabilities: 380000,
        total_equity: 10000,
        total_revenue: 350000,
        cost_of_goods_sold: 280000,
        gross_profit: 70000,
        operating_profit_ebit: -45000,
        net_profit: -70000,
        operating_cash_flow: -35000,
        interest_expense: 35000,
      });
      setIncludeNetwork(false);
    } else if (presetType === "incomplete") {
      // Zero revenue triggers incomplete gate
      setFormData({
        fiscal_year: 2023,
        total_assets: 0,
        current_assets: 0,
        cash_and_equivalents: 0,
        inventory: 0,
        accounts_receivable: 0,
        total_liabilities: 0,
        short_term_liabilities: 0,
        total_equity: 0,
        total_revenue: 0,
        cost_of_goods_sold: 0,
        gross_profit: 0,
        operating_profit_ebit: 0,
        net_profit: 0,
        operating_cash_flow: 0,
        interest_expense: 0,
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSmeId) {
      setError("Please select a target SME.");
      return;
    }

    setSubmitting(true);
    setError(null);

    const statement: StatementPeriod = {
      fiscal_year: formData.fiscal_year,
      total_assets: formData.total_assets,
      current_assets: formData.current_assets,
      cash_and_equivalents: formData.cash_and_equivalents,
      inventory: formData.inventory,
      accounts_receivable: formData.accounts_receivable,
      total_liabilities: formData.total_liabilities,
      short_term_liabilities: formData.short_term_liabilities,
      total_equity: formData.total_equity,
      total_revenue: formData.total_revenue,
      cost_of_goods_sold: formData.cost_of_goods_sold,
      gross_profit: formData.gross_profit,
      operating_profit_ebit: formData.operating_profit_ebit,
      net_profit: formData.net_profit,
      operating_cash_flow: formData.operating_cash_flow,
      interest_expense: formData.interest_expense,
    };

    const payload: {
      sme_id: string;
      statements: StatementPeriod[];
      network_neighbors?: string[];
      network_edges?: [number, number][];
    } = {
      sme_id: selectedSmeId,
      statements: [statement],
    };

    if (includeNetwork) {
      payload.network_neighbors = ["SUPPLIER_POLAND_01", "BUYER_LOGISTICS_02"];
      payload.network_edges = [
        [0, 1],
        [1, 0],
      ];
    }

    try {
      const res = await api.runAssessment(payload);
      router.push(`/bank/assessments/${res.assessment_id}`);
    } catch (err: unknown) {
      console.error("Assessment run error:", err);
      const msg = err instanceof Error ? err.message : "Assessment scoring execution failed.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-8 space-y-8">
      {/* Back Link */}
      <Link
        href="/bank"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Portfolio
      </Link>

      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-black text-zinc-900 dark:text-zinc-100 flex items-center gap-2.5">
          <Activity className="w-7 h-7 text-indigo-600" />
          SME Credit Risk Assessment Wizard
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Executes completeness gating, 64-ratio tabular scoring, GNN ego-network inference,
          multi-modal fusion, tabular SHAP attributions, and 4-scenario stress testing.
        </p>
      </div>

      {/* Presets Bar */}
      <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-indigo-900 dark:text-indigo-200 uppercase tracking-wider">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          Quick Test Presets (Instant Evaluation)
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => applyPreset("healthy")}
            className="px-3 py-1.5 rounded-lg bg-white dark:bg-zinc-850 text-xs font-bold text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 hover:bg-emerald-50 transition shadow-2xs"
          >
            ✓ Healthy SME (Band A / Lower Risk)
          </button>
          <button
            type="button"
            onClick={() => applyPreset("distressed")}
            className="px-3 py-1.5 rounded-lg bg-white dark:bg-zinc-850 text-xs font-bold text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800 hover:bg-rose-50 transition shadow-2xs"
          >
            ⚠ Distressed SME (Band D / High Risk)
          </button>
          <button
            type="button"
            onClick={() => applyPreset("incomplete")}
            className="px-3 py-1.5 rounded-lg bg-white dark:bg-zinc-850 text-xs font-bold text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-800 hover:bg-purple-50 transition shadow-2xs"
          >
            ✕ Incomplete Gate (Rule 4.2 Inconclusive)
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs text-rose-800 dark:text-rose-200 space-y-1">
            <span className="font-bold">Assessment Failed:</span> {error}
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Target SME */}
        <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-indigo-600" />
            1. Select Target Borrower SME
          </h2>

          <div>
            <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
              Registered SME Account
            </label>
            {loadingSmes ? (
              <div className="text-xs text-zinc-500 py-2">Loading portfolio SMEs...</div>
            ) : (
              <select
                value={selectedSmeId}
                onChange={(e) => setSelectedSmeId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              >
                {smes.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.legal_name} (Tax ID: {s.tax_id}) — {s.sector || "General"}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Step 2: Financial Statements */}
        <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs space-y-6">
          <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-indigo-600" />
            2. Annual Financial Statement Figures (PLN)
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Fiscal Year
              </label>
              <input
                type="number"
                value={formData.fiscal_year}
                onChange={(e) => handleInputChange("fiscal_year", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Total Revenue
              </label>
              <input
                type="number"
                value={formData.total_revenue}
                onChange={(e) => handleInputChange("total_revenue", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Operating Profit (EBIT)
              </label>
              <input
                type="number"
                value={formData.operating_profit_ebit}
                onChange={(e) => handleInputChange("operating_profit_ebit", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Total Assets
              </label>
              <input
                type="number"
                value={formData.total_assets}
                onChange={(e) => handleInputChange("total_assets", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Current Assets
              </label>
              <input
                type="number"
                value={formData.current_assets}
                onChange={(e) => handleInputChange("current_assets", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Cash & Equivalents
              </label>
              <input
                type="number"
                value={formData.cash_and_equivalents}
                onChange={(e) => handleInputChange("cash_and_equivalents", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Total Liabilities
              </label>
              <input
                type="number"
                value={formData.total_liabilities}
                onChange={(e) => handleInputChange("total_liabilities", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Short-Term Liabilities
              </label>
              <input
                type="number"
                value={formData.short_term_liabilities}
                onChange={(e) => handleInputChange("short_term_liabilities", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Total Equity
              </label>
              <input
                type="number"
                value={formData.total_equity}
                onChange={(e) => handleInputChange("total_equity", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Net Profit / (Loss)
              </label>
              <input
                type="number"
                value={formData.net_profit}
                onChange={(e) => handleInputChange("net_profit", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Operating Cash Flow
              </label>
              <input
                type="number"
                value={formData.operating_cash_flow}
                onChange={(e) => handleInputChange("operating_cash_flow", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
                Interest Expense
              </label>
              <input
                type="number"
                value={formData.interest_expense}
                onChange={(e) => handleInputChange("interest_expense", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Step 3: Network Diffusion Context */}
        <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs space-y-3">
          <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Share2 className="w-4 h-4 text-indigo-600" />
            3. Network Graph Diffusion Context
          </h2>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="network-toggle"
              checked={includeNetwork}
              onChange={(e) => setIncludeNetwork(e.target.checked)}
              className="w-4 h-4 text-indigo-600 rounded-sm border-zinc-300 focus:ring-indigo-500"
            />
            <label htmlFor="network-toggle" className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
              Include synthetic trade counterparty graph (GNN ego-network diffusion)
            </label>
          </div>
          <p className="text-xs text-zinc-500">
            If unchecked, RIPPLE activates cold-start isolated node policy (zero fabricated graph PD per AGENTS.md Rule 4.2).
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Link
            href="/bank"
            className="px-5 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 text-sm font-semibold text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-850 transition"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-sm shadow-md transition"
          >
            {submitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Evaluating Multi-Modal Risk...
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" /> Run Assessment
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
