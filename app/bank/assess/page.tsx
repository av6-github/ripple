"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { SmeProfile, StatementPeriod, LoanApplicationRecord } from "@/lib/types";
import {
  Activity,
  ArrowLeft,
  Building2,
  Sparkles,
  AlertCircle,
  FileSpreadsheet,
  Share2,
  FileText,
  CheckCircle,
} from "lucide-react";

import { RoleGuard } from "@/app/components/RoleGuard";

// Wrap in Suspense to satisfy Next.js useSearchParams client component requirement
export default function AssessmentWizardPage() {
  return (
    <RoleGuard allowedRoles={["bank_officer", "admin"]}>
      <Suspense
        fallback={
          <div className="mx-auto max-w-4xl py-20 text-center">
            <div className="w-8 h-8 border-4 border-[#2f6690] border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-sm text-[#2f6690] mt-2 font-medium">Loading wizard...</p>
          </div>
        }
      >
        <AssessmentWizardContent />
      </Suspense>
    </RoleGuard>
  );
}

function AssessmentWizardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const applicationId = searchParams.get("application_id") || "";
  const initialSmeId = searchParams.get("sme_id") || "";

  const [smes, setSmes] = useState<SmeProfile[]>([]);
  const [selectedSmeId, setSelectedSmeId] = useState<string>(initialSmeId);
  const [loanApp, setLoanApp] = useState<LoanApplicationRecord | null>(null);
  const [loadingApp, setLoadingApp] = useState(false);
  const [loadingSmes, setLoadingSmes] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Network context options & live AuraDB counterparties
  const [includeNetwork, setIncludeNetwork] = useState(true);
  const [liveCounterparties, setLiveCounterparties] = useState<{
    sme_id: string;
    tax_id: string;
    count: number;
    counterparties: Array<{
      name: string;
      direction: string;
      tax_id?: string;
      is_registered_sme?: boolean;
    }>;
    edges: [number, number][];
  } | null>(null);
  const [loadingCounterparties, setLoadingCounterparties] = useState(false);

  // Financial line items state (latest annual statement) - Calibrated to Polish benchmark
  const [formData, setFormData] = useState({
    fiscal_year: 2023,
    total_assets: 980000,
    current_assets: 420000,
    cash_and_equivalents: 65000,
    inventory: 45000,
    accounts_receivable: 210000,
    total_liabilities: 490000,
    short_term_liabilities: 310000,
    total_equity: 490000,
    total_revenue: 1450000,
    cost_of_goods_sold: 890000,
    gross_profit: 560000,
    operating_profit_ebit: 125000,
    net_profit: 72000,
    operating_cash_flow: 88000,
    interest_expense: 28000,
  });

  const [baselineStatement, setBaselineStatement] = useState<StatementPeriod | null>(null);

  useEffect(() => {
    if (!applicationId) return;
    setLoadingApp(true);
    api
      .getLoanApplication(applicationId)
      .then((res) => {
        if (res?.application) {
          const app = res.application;
          setLoanApp(app);
          if (app.sme_id) {
            setSelectedSmeId(app.sme_id);
          }
          setFormData((prev) => ({
            ...prev,
            total_revenue: app.self_reported_revenue ?? prev.total_revenue,
            total_assets: app.self_reported_assets ?? prev.total_assets,
            total_liabilities: app.self_reported_liabilities ?? prev.total_liabilities,
            total_equity: app.self_reported_equity ?? prev.total_equity,
            net_profit: app.self_reported_net_profit ?? prev.net_profit,
            cash_and_equivalents: app.self_reported_cash ?? prev.cash_and_equivalents,
            current_assets: Math.round((app.self_reported_assets ?? prev.total_assets) * 0.45),
            short_term_liabilities: Math.round((app.self_reported_liabilities ?? prev.total_liabilities) * 0.60),
            operating_profit_ebit: Math.round((app.self_reported_net_profit ?? prev.net_profit) * 1.3),
            gross_profit: Math.round((app.self_reported_revenue ?? prev.total_revenue) * 0.38),
            cost_of_goods_sold: Math.round((app.self_reported_revenue ?? prev.total_revenue) * 0.62),
          }));
        }
      })
      .catch((err) => console.error("Could not load application details:", err))
      .finally(() => setLoadingApp(false));
  }, [applicationId]);

  useEffect(() => {
    api
      .listSmes()
      .then((data) => {
        setSmes(data);
        if (data.length > 0 && !applicationId) {
          setSelectedSmeId((prev) => prev || data[0].id);
        }
      })
      .catch((err) => console.error("Error fetching SMEs:", err))
      .finally(() => setLoadingSmes(false));
  }, [applicationId]);

  // Dynamically load live AuraDB counterparties and baseline financial statement whenever selectedSmeId changes
  useEffect(() => {
    if (!selectedSmeId) {
      setLiveCounterparties(null);
      setBaselineStatement(null);
      return;
    }
    setLoadingCounterparties(true);
    api
      .getSmeCounterparties(selectedSmeId)
      .then((data) => {
        setLiveCounterparties(data);
      })
      .catch((err) => {
        console.warn("Could not fetch AuraDB counterparties, will default to backend resolution:", err);
        setLiveCounterparties(null);
      })
      .finally(() => setLoadingCounterparties(false));

    // Fetch SME's actual baseline financial statement from backend
    api
      .getSmeProfile(selectedSmeId)
      .then((res: any) => {
        if (res?.latest_statement) {
          const stmt = res.latest_statement;
          setBaselineStatement(stmt);
          setFormData({
            fiscal_year: stmt.fiscal_year || 2023,
            total_assets: stmt.total_assets || 0,
            current_assets: stmt.current_assets || 0,
            cash_and_equivalents: stmt.cash_and_equivalents || 0,
            inventory: stmt.inventory || 0,
            accounts_receivable: stmt.accounts_receivable || 0,
            total_liabilities: stmt.total_liabilities || 0,
            short_term_liabilities: stmt.short_term_liabilities || 0,
            total_equity: stmt.total_equity || 0,
            total_revenue: stmt.total_revenue || 0,
            cost_of_goods_sold: stmt.cost_of_goods_sold || 0,
            gross_profit: stmt.gross_profit || 0,
            operating_profit_ebit: stmt.operating_profit_ebit || 0,
            net_profit: stmt.net_profit || 0,
            operating_cash_flow: stmt.operating_cash_flow || 0,
            interest_expense: stmt.interest_expense || 0,
          });
        }
      })
      .catch((err) => {
        console.warn("Could not load baseline statement for SME:", err);
      });
  }, [selectedSmeId]);

  const handleInputChange = (field: string, val: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: field === "fiscal_year" ? parseInt(val) || 2023 : parseFloat(val) || 0,
    }));
  };

  // Demo presets: calculates proportional macro shocks scaled to the selected company's actual balance sheet
  const applyPreset = (presetType: "healthy" | "distressed" | "incomplete") => {
    if (presetType === "healthy") {
      if (baselineStatement) {
        setFormData({
          fiscal_year: baselineStatement.fiscal_year || 2023,
          total_assets: baselineStatement.total_assets || 0,
          current_assets: baselineStatement.current_assets || 0,
          cash_and_equivalents: baselineStatement.cash_and_equivalents || 0,
          inventory: baselineStatement.inventory || 0,
          accounts_receivable: baselineStatement.accounts_receivable || 0,
          total_liabilities: baselineStatement.total_liabilities || 0,
          short_term_liabilities: baselineStatement.short_term_liabilities || 0,
          total_equity: baselineStatement.total_equity || 0,
          total_revenue: baselineStatement.total_revenue || 0,
          cost_of_goods_sold: baselineStatement.cost_of_goods_sold || 0,
          gross_profit: baselineStatement.gross_profit || 0,
          operating_profit_ebit: baselineStatement.operating_profit_ebit || 0,
          net_profit: baselineStatement.net_profit || 0,
          operating_cash_flow: baselineStatement.operating_cash_flow || 0,
          interest_expense: baselineStatement.interest_expense || 0,
        });
      } else {
        setFormData({
          fiscal_year: 2023,
          total_assets: 1100000,
          current_assets: 520000,
          cash_and_equivalents: 95000,
          inventory: 120000,
          accounts_receivable: 260000,
          total_liabilities: 480000,
          short_term_liabilities: 260000,
          total_equity: 620000,
          total_revenue: 1650000,
          cost_of_goods_sold: 1020000,
          gross_profit: 630000,
          operating_profit_ebit: 185000,
          net_profit: 118000,
          operating_cash_flow: 145000,
          interest_expense: 22000,
        });
      }
      setIncludeNetwork(true);
    } else if (presetType === "distressed") {
      // Proportional economic distress shock based on this specific SME's baseline financials
      const base = baselineStatement || formData;
      const baseRev = base.total_revenue || 1000000;
      const baseCogs = base.cost_of_goods_sold || 600000;
      const rev = Math.round(baseRev * 0.70); // -30% revenue shock
      const cogs = Math.round(baseCogs * 0.90); // sticky operating costs
      const gross = rev - cogs;
      const opexDiff = Math.max(0, (base.gross_profit || 0) - (base.operating_profit_ebit || 0));
      const ebit = Math.round(gross - opexDiff * 1.05); // slight opex inflation
      const interest = Math.round((base.interest_expense || 20000) * 1.30); // benchmark rate pressure
      const net = ebit - interest;
      const cash = Math.max(5000, Math.round((base.cash_and_equivalents || 40000) * 0.35)); // -65% liquidity burn
      const ar = Math.round((base.accounts_receivable || 120000) * 1.35); // +35% customer receivables stretch (DSO)
      const inv = Math.round((base.inventory || 50000) * 1.10); // slow-moving inventory build-up
      const stLiab = Math.round((base.short_term_liabilities || 200000) * 1.25); // +25% working capital strain
      const totLiab = Math.round((base.total_liabilities || 300000) * 1.20);
      const equity = Math.max(1000, Math.round((base.total_equity || 200000) + (net - (base.net_profit || 0))));
      const totAssets = equity + totLiab;
      const currAssets = cash + ar + inv;
      const ocf = Math.round(net + ((base.operating_cash_flow || 0) - (base.net_profit || 0)) * 0.4);

      setFormData({
        fiscal_year: base.fiscal_year || 2023,
        total_assets: totAssets,
        current_assets: currAssets,
        cash_and_equivalents: cash,
        inventory: inv,
        accounts_receivable: ar,
        total_liabilities: totLiab,
        short_term_liabilities: stLiab,
        total_equity: equity,
        total_revenue: rev,
        cost_of_goods_sold: cogs,
        gross_profit: gross,
        operating_profit_ebit: ebit,
        net_profit: net,
        operating_cash_flow: ocf,
        interest_expense: interest,
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
      application_id?: string;
    } = {
      sme_id: selectedSmeId,
      statements: [statement],
    };

    if (applicationId) {
      payload.application_id = applicationId;
    }

    if (includeNetwork) {
      if (liveCounterparties && liveCounterparties.counterparties.length > 0) {
        payload.network_neighbors = liveCounterparties.counterparties.map((c) => c.name);
        payload.network_edges = liveCounterparties.edges;
      }
      // Note: If liveCounterparties is not populated, omitting network_neighbors triggers
      // AssessmentService's dynamic Neo4j AuraDB enrichment directly on the backend!
    } else {
      payload.network_neighbors = [];
      payload.network_edges = [];
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
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-8 space-y-8 text-[#16425b]">
      {/* Back Link */}
      <Link
        href="/bank"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2f6690] hover:text-[#16425b] transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Portfolio
      </Link>

      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-black text-[#16425b] flex items-center gap-2.5">
          <Activity className="w-7 h-7 text-[#2f6690]" />
          SME Credit Risk Assessment Wizard
        </h1>
        <p className="text-sm text-[#2f6690]">
          Executes completeness gating, 64-ratio tabular scoring, GNN ego-network inference,
          multi-modal fusion, tabular SHAP attributions, and 4-scenario stress testing.
        </p>
      </div>

      {/* Loan Application Underwriting Context Banner */}
      {applicationId && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-300 space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-900 uppercase tracking-wider">
              <FileText className="w-4 h-4 text-emerald-700" />
              Underwriting Loan Application #{applicationId.slice(0, 8)}
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-200 text-emerald-900 border border-emerald-400">
              {loanApp?.status || "IN_REVIEW"}
            </span>
          </div>
          {loanApp ? (
            <div className="text-xs text-emerald-950 grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono">
              <div>
                <span className="text-emerald-700 block text-[10px] uppercase font-sans">Facility</span>
                <strong>{loanApp.facility_type.replace(/_/g, " ")}</strong>
              </div>
              <div>
                <span className="text-emerald-700 block text-[10px] uppercase font-sans">Requested Amount</span>
                <strong>{loanApp.requested_amount.toLocaleString()} PLN</strong>
              </div>
              <div>
                <span className="text-emerald-700 block text-[10px] uppercase font-sans">Tenor</span>
                <strong>{loanApp.tenor_months} months</strong>
              </div>
              <div>
                <span className="text-emerald-700 block text-[10px] uppercase font-sans">Borrower</span>
                <strong>{loanApp.legal_name || loanApp.contact_name || "Applicant SME"}</strong>
              </div>
            </div>
          ) : (
            <p className="text-xs text-emerald-800">
              Loading borrower self-reported financial indicators...
            </p>
          )}
          <p className="text-[11px] text-emerald-800 pt-1">
            ✓ Financial metrics below are pre-populated with self-reported figures from this loan application and will be reconciled against KRS records.
          </p>
        </div>
      )}

      {/* Presets Bar */}
      <div className="p-4 rounded-2xl bg-[#3a7ca5]/15 border border-[#3a7ca5]/35 space-y-2 shadow-xs">
        <div className="flex items-center gap-2 text-xs font-bold text-[#16425b] uppercase tracking-wider">
          <Sparkles className="w-4 h-4 text-[#2f6690]" />
          Quick Test Presets (Instant Evaluation)
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => applyPreset("healthy")}
            className="px-3 py-1.5 rounded-lg bg-white text-xs font-bold text-[#16425b] border border-[#3a7ca5]/40 hover:bg-[#81c3d7]/20 transition shadow-2xs"
          >
            ✓ Healthy SME (Band B / Calibrated Benchmark)
          </button>
          <button
            type="button"
            onClick={() => applyPreset("distressed")}
            className="px-3 py-1.5 rounded-lg bg-white text-xs font-bold text-rose-800 border border-rose-300 hover:bg-rose-50 transition shadow-2xs"
          >
            ⚠ Distressed SME (Band D / High Risk)
          </button>
          <button
            type="button"
            onClick={() => applyPreset("incomplete")}
            className="px-3 py-1.5 rounded-lg bg-white text-xs font-bold text-[#2f6690] border border-[#3a7ca5]/40 hover:bg-[#d9dcd6] transition shadow-2xs"
          >
            ✕ Incomplete Gate (Rule 4.2 Inconclusive)
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-300 flex items-start gap-3 shadow-xs">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs text-rose-900 space-y-1">
            <span className="font-bold">Assessment Failed:</span> {error}
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Target SME */}
        <div className="p-6 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-[#16425b] flex items-center gap-2">
            <Building2 className="w-4 h-4 text-[#2f6690]" />
            1. Select Target Borrower SME
          </h2>

          <div>
            <label className="block text-xs font-semibold text-[#16425b] mb-1">
              Registered SME Account
            </label>
            {loadingSmes ? (
              <div className="text-xs text-[#2f6690] py-2">Loading portfolio SMEs...</div>
            ) : (
              <select
                value={selectedSmeId}
                onChange={(e) => setSelectedSmeId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-[#16425b] text-sm font-medium focus:ring-2 focus:ring-[#3a7ca5]"
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
        <div className="p-6 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-6">
          <h2 className="text-base font-bold text-[#16425b] flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-[#2f6690]" />
            2. Annual Financial Statement Figures (PLN)
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Fiscal Year
              </label>
              <input
                type="number"
                value={formData.fiscal_year}
                onChange={(e) => handleInputChange("fiscal_year", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Total Revenue
              </label>
              <input
                type="number"
                value={formData.total_revenue}
                onChange={(e) => handleInputChange("total_revenue", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Operating Profit (EBIT)
              </label>
              <input
                type="number"
                value={formData.operating_profit_ebit}
                onChange={(e) => handleInputChange("operating_profit_ebit", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Total Assets
              </label>
              <input
                type="number"
                value={formData.total_assets}
                onChange={(e) => handleInputChange("total_assets", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Current Assets
              </label>
              <input
                type="number"
                value={formData.current_assets}
                onChange={(e) => handleInputChange("current_assets", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Cash & Equivalents
              </label>
              <input
                type="number"
                value={formData.cash_and_equivalents}
                onChange={(e) => handleInputChange("cash_and_equivalents", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Total Liabilities
              </label>
              <input
                type="number"
                value={formData.total_liabilities}
                onChange={(e) => handleInputChange("total_liabilities", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Short-Term Liabilities
              </label>
              <input
                type="number"
                value={formData.short_term_liabilities}
                onChange={(e) => handleInputChange("short_term_liabilities", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Total Equity
              </label>
              <input
                type="number"
                value={formData.total_equity}
                onChange={(e) => handleInputChange("total_equity", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Net Profit / (Loss)
              </label>
              <input
                type="number"
                value={formData.net_profit}
                onChange={(e) => handleInputChange("net_profit", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Operating Cash Flow
              </label>
              <input
                type="number"
                value={formData.operating_cash_flow}
                onChange={(e) => handleInputChange("operating_cash_flow", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#16425b] mb-1">
                Interest Expense
              </label>
              <input
                type="number"
                value={formData.interest_expense}
                onChange={(e) => handleInputChange("interest_expense", e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#3a7ca5]/40 bg-white text-[#16425b] font-mono"
              />
            </div>
          </div>
        </div>

        {/* Step 3: Network Diffusion Context */}
        <div className="p-6 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[#16425b] flex items-center gap-2">
              <Share2 className="w-4 h-4 text-[#2f6690]" />
              3. Network Graph Diffusion Context (Neo4j AuraDB)
            </h2>
            {loadingCounterparties && (
              <span className="text-xs text-[#2f6690] font-medium flex items-center gap-1.5">
                <div className="w-3 h-3 border-2 border-[#2f6690] border-t-transparent rounded-full animate-spin"></div>
                Querying AuraDB...
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="network-toggle"
              checked={includeNetwork}
              onChange={(e) => setIncludeNetwork(e.target.checked)}
              className="w-4 h-4 text-[#2f6690] rounded-sm border-[#3a7ca5]/40 focus:ring-[#3a7ca5]"
            />
            <label htmlFor="network-toggle" className="text-sm font-semibold text-[#16425b]">
              Include trade counterparty graph (GNN ego-network diffusion via Neo4j AuraDB)
            </label>
          </div>

          {includeNetwork && liveCounterparties && (
            <div className="mt-3 p-4 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-[#16425b] flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#2f6690] inline-block animate-pulse"></span>
                  Live AuraDB Graph Topology: {liveCounterparties.count} Counterparties
                </span>
                <span className="font-mono text-[#2f6690]">Tax ID: {liveCounterparties.tax_id}</span>
              </div>

              {liveCounterparties.counterparties.length > 0 ? (
                <div className="space-y-1.5 pt-1">
                  {liveCounterparties.counterparties.map((cp, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded-lg bg-white border border-[#3a7ca5]/30"
                    >
                      <span className="font-medium text-[#16425b] truncate pr-2">
                        {cp.name}
                      </span>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[#3a7ca5]/20 text-[#16425b] border border-[#3a7ca5]/30">
                          {cp.direction}
                        </span>
                        {cp.is_registered_sme && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-[#81c3d7]/30 text-[#16425b] border border-[#3a7ca5]/40">
                            Registered SME
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                  <p className="text-[11px] text-[#2f6690] pt-1">
                    Topology retrieved live from Neo4j AuraDB. All synthetic commercial links comply with Rule 4.4 (<code className="font-mono bg-white px-1 rounded border border-[#3a7ca5]/30">is_synthetic = true</code>).
                  </p>
                </div>
              ) : (
                <p className="text-xs text-amber-800">
                  No trade counterparties found for Tax ID {liveCounterparties.tax_id} in AuraDB. GNN will run under isolated node / cold-start policy.
                </p>
              )}
            </div>
          )}

          <p className="text-xs text-[#2f6690]">
            If unchecked, RIPPLE activates cold-start isolated node policy (zero fabricated graph PD per AGENTS.md Rule 4.2).
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Link
            href="/bank"
            className="px-5 py-2.5 rounded-xl border border-[#3a7ca5]/40 text-sm font-semibold text-[#16425b] bg-white hover:bg-[#d9dcd6] transition shadow-2xs"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#2f6690] hover:bg-[#16425b] disabled:opacity-50 text-white font-bold text-sm shadow-md transition"
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
