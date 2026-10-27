"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { IngestionJobResult, SmeProfile } from "@/lib/types";
import {
  FileSpreadsheet,
  ArrowLeft,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShieldCheck,
  Download,
  Building2,
  X,
  Sparkles,
  RotateCcw,
  BadgeCheck,
  ChevronRight,
} from "lucide-react";
import { RoleGuard } from "@/app/components/RoleGuard";

interface SamplePreset {
  title: string;
  filename: string;
  badge: string;
  badgeColor: string;
  description: string;
  defaultSmeMatch?: string;
}

const SAMPLE_PRESETS: SamplePreset[] = [
  {
    title: "Healthy Tech SME (CSV)",
    filename: "healthy_tech_sme.csv",
    badge: "Low Risk Profile",
    badgeColor: "bg-[#81c3d7]/30 text-[#16425b] border border-[#3a7ca5]/40",
    description: "Revenue: 1.45M PLN | Equity: 490k PLN | Robust liquidity with positive working capital.",
    defaultSmeMatch: "PolTech",
  },
  {
    title: "Moderate Industrial SME (CSV)",
    filename: "moderate_industrial_sme.csv",
    badge: "Operating Benchmark",
    badgeColor: "bg-[#3a7ca5]/20 text-[#16425b] border border-[#3a7ca5]/40",
    description: "Revenue: 920k PLN | Assets: 850k PLN | Heavy metallurgy fabricator with balanced cash flow.",
    defaultSmeMatch: "Silesia",
  },
  {
    title: "Distressed Retail SME (CSV)",
    filename: "distressed_retail_sme.csv",
    badge: "Elevated Risk Flags",
    badgeColor: "bg-amber-100 text-[#16425b] border border-amber-300",
    description: "Revenue: 680k PLN | Liabilities: 710k PLN | Tight working capital & leverage flags.",
    defaultSmeMatch: "Baltic",
  },
  {
    title: "Corporate Balance Sheet (XLSX)",
    filename: "sample_financial_statement.xlsx",
    badge: "Excel Spreadsheet",
    badgeColor: "bg-[#2f6690]/20 text-[#16425b] border border-[#2f6690]/40",
    description: "Standard multi-line Excel financial ledger covering assets, liabilities, and income items.",
    defaultSmeMatch: "Kraków",
  },
];

export default function SmeUploadPage() {
  const { smeId } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // SME Selection
  const [smes, setSmes] = useState<SmeProfile[]>([]);
  const [selectedSmeId, setSelectedSmeId] = useState<string>("");
  const [loadingSmes, setLoadingSmes] = useState<boolean>(true);

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);

  // Result & Feedback State
  const [ingestionResult, setIngestionResult] = useState<IngestionJobResult | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch available SMEs on mount
  useEffect(() => {
    let mounted = true;
    api
      .listSmes()
      .then((data) => {
        if (!mounted) return;
        setSmes(data);
        if (data.length > 0) {
          const match = smeId ? data.find((s) => s.id === smeId) : data[0];
          setSelectedSmeId(match ? match.id : data[0].id);
        } else if (smeId) {
          setSelectedSmeId(smeId);
        }
      })
      .catch((e) => {
        console.warn("Could not list all portfolio SMEs (role isolated):", e);
        if (smeId) setSelectedSmeId(smeId);
      })
      .finally(() => {
        if (mounted) setLoadingSmes(false);
      });
    return () => {
      mounted = false;
    };
  }, [smeId]);

  // Handle Drag & Drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
      setUploadSuccess(null);
      setError(null);
      setIngestionResult(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadSuccess(null);
      setError(null);
      setIngestionResult(null);
    }
  };

  // Quick-load a ready-to-use sample file
  const handleLoadSample = async (preset: SamplePreset) => {
    setError(null);
    setUploadSuccess(null);
    setIngestionResult(null);
    setLoadingSample(preset.filename);

    try {
      const res = await fetch(`/sample_statements/${preset.filename}`);
      if (!res.ok) throw new Error(`Could not load sample file (${res.status})`);
      const blob = await res.blob();
      const file = new File(
        [blob],
        preset.filename,
        {
          type: preset.filename.endsWith(".xlsx")
            ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            : "text/csv",
        }
      );
      setSelectedFile(file);

      // Auto-select corresponding SME if available
      if (preset.defaultSmeMatch && smes.length > 0) {
        const match = smes.find((s) =>
          s.legal_name.toLowerCase().includes(preset.defaultSmeMatch!.toLowerCase())
        );
        if (match) setSelectedSmeId(match.id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sample statement.");
    } finally {
      setLoadingSample(null);
    }
  };

  // Form Submit Handler
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      setError("Please choose or drag a financial statement file first, or click one of the ready-to-use sample cards above.");
      return;
    }

    const targetSmeId = selectedSmeId || smeId;
    if (!targetSmeId) {
      setError("Please select a target SME from the list above before ingesting.");
      return;
    }

    setUploading(true);
    setError(null);
    setUploadSuccess(null);
    setIngestionResult(null);

    try {
      const response = await api.uploadFinancialFile(targetSmeId, selectedFile);
      setIngestionResult(response.job);
      setUploadSuccess(
        `Successfully ingested and verified "${selectedFile.name}". Statements extracted and validated with full provenance tracking.`
      );
    } catch (err: unknown) {
      console.error(err);
      const msg = err instanceof Error ? err.message : "Failed to upload financial statement.";
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setIngestionResult(null);
    setUploadSuccess(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const selectedSme = smes.find((s) => s.id === selectedSmeId);

  return (
    <RoleGuard allowedRoles={["sme_user", "bank_officer", "admin"]}>
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8 space-y-8 text-[#16425b]">
      {/* Back Link */}
      <Link
        href="/sme"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2f6690] hover:text-[#16425b] transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to SME Readiness Dashboard
      </Link>

      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-black text-[#16425b] flex items-center gap-2.5">
          <FileSpreadsheet className="w-8 h-8 text-[#2f6690]" />
          Financial Statement Ingestion & Provenance Engine
        </h1>
        <p className="text-sm text-[#2f6690]">
          Upload balance sheets and income statements (.csv, .xlsx, .pdf, .arff) with automated provenance tracking and completeness validation.
        </p>
      </div>

      {/* Target SME Selector Card */}
      <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold uppercase tracking-wider text-[#16425b] flex items-center gap-2">
            <Building2 className="w-4 h-4 text-[#3a7ca5]" />
            Target SME Profile (Recipient of Ingested Records)
          </label>
          {selectedSme && (
            <span className="text-2xs font-mono px-2 py-0.5 rounded bg-[#d9dcd6]/60 border border-[#3a7ca5]/30 text-[#16425b]">
              Tax ID: {selectedSme.tax_id}
            </span>
          )}
        </div>

        <select
          value={selectedSmeId}
          onChange={(e) => setSelectedSmeId(e.target.value)}
          disabled={loadingSmes}
          className="w-full text-xs font-medium px-3 py-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-[#16425b] focus:outline-none focus:ring-2 focus:ring-[#3a7ca5]"
        >
          {loadingSmes ? (
            <option>Loading registered SMEs...</option>
          ) : smes.length > 0 ? (
            smes.map((s) => (
              <option key={s.id} value={s.id}>
                {s.legal_name} ({s.industry || s.sector || "General Commercial"})
              </option>
            ))
          ) : (
            <option value={selectedSmeId || ""}>
              Active Registered SME Context ({selectedSmeId || "Connected"})
            </option>
          )}
        </select>
      </div>

      {/* Ready-to-Use Sample Statements Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#16425b] flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#3a7ca5]" />
            Ready-to-Use Sample Statements (1-Click Fill)
          </h2>
          <span className="text-2xs text-[#2f6690]">Click any card to load instantly</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {SAMPLE_PRESETS.map((preset) => (
            <div
              key={preset.filename}
              className="p-3.5 rounded-xl bg-white/90 border border-[#3a7ca5]/30 hover:border-[#2f6690] transition shadow-xs flex flex-col justify-between space-y-3"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className={`text-3xs font-bold px-2 py-0.5 rounded-full ${preset.badgeColor}`}>
                    {preset.badge}
                  </span>
                  <a
                    href={`/sample_statements/${preset.filename}`}
                    download={preset.filename}
                    title="Download file to inspect"
                    className="text-[#2f6690] hover:text-[#16425b] p-1 rounded"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </a>
                </div>
                <h3 className="text-xs font-bold text-[#16425b]">
                  {preset.title}
                </h3>
                <p className="text-3xs text-[#2f6690] leading-relaxed">
                  {preset.description}
                </p>
              </div>

              <button
                type="button"
                onClick={() => handleLoadSample(preset)}
                disabled={loadingSample === preset.filename}
                className="w-full text-center py-1.5 px-3 rounded-lg bg-[#d9dcd6] hover:bg-[#3a7ca5] text-[#16425b] hover:text-white text-2xs font-bold transition flex items-center justify-center gap-1.5"
              >
                {loadingSample === preset.filename ? (
                  <div className="w-3 h-3 border-2 border-[#16425b] border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <UploadCloud className="w-3.5 h-3.5 text-[#2f6690]" /> Use This Sample
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Upload Zone & Form */}
      <form onSubmit={handleUpload} className="space-y-6">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`p-8 rounded-2xl bg-white/90 border-2 border-dashed text-center space-y-4 cursor-pointer transition ${
            isDragging
              ? "border-[#2f6690] bg-[#81c3d7]/20 scale-[1.01]"
              : "border-[#3a7ca5]/50 hover:border-[#2f6690]"
          }`}
        >
          <div className="w-12 h-12 rounded-full bg-[#3a7ca5]/15 text-[#2f6690] flex items-center justify-center mx-auto shadow-2xs">
            <UploadCloud className="w-6 h-6" />
          </div>

          <div className="space-y-1">
            <h3 className="text-sm font-bold text-[#16425b]">
              Drag and drop your financial statement file, or click anywhere to browse
            </h3>
            <p className="text-xs text-[#2f6690]">
              Supported formats: CSV, Excel (.xlsx, .xls), PDF, or Polish ARFF (up to 10 MB)
            </p>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            id="statement-upload"
            onChange={handleFileChange}
            accept=".csv,.xlsx,.xls,.pdf,.arff"
            className="hidden"
          />

          {/* Selected File Pill */}
          {selectedFile ? (
            <div
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#81c3d7]/20 border border-[#3a7ca5]/40 text-xs text-[#16425b] font-mono shadow-xs"
            >
              <FileText className="w-4 h-4 text-[#2f6690]" />
              <span className="font-bold">{selectedFile.name}</span>
              <span className="text-[#2f6690]">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              <button
                type="button"
                onClick={handleReset}
                className="ml-2 text-[#2f6690] hover:text-rose-600 transition"
                title="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div>
              <span className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-[#3a7ca5] hover:bg-[#2f6690] text-white text-xs font-bold transition shadow-xs">
                Choose File from Computer
              </span>
            </div>
          )}
        </div>

        {/* Error Notification */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-300 text-xs text-rose-900 flex items-center gap-2 shadow-xs">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Success Toast */}
        {uploadSuccess && (
          <div className="p-4 rounded-xl bg-[#81c3d7]/20 border border-[#3a7ca5]/40 text-xs text-[#16425b] flex items-center gap-2 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-[#2f6690] shrink-0" />
            <span>{uploadSuccess}</span>
          </div>
        )}

        {/* Ingest Action Button */}
        <div className="flex items-center justify-between">
          <p className="text-3xs text-[#2f6690]">
            Rule 4.3 Provenance: Line items will be tagged with <code className="font-mono bg-white/70 px-1 py-0.5 rounded border border-[#3a7ca5]/30">source_type=extracted_file</code> and <code className="font-mono bg-white/70 px-1 py-0.5 rounded border border-[#3a7ca5]/30">confidence=verified</code>.
          </p>

          <button
            type="submit"
            disabled={uploading}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#2f6690] hover:bg-[#16425b] disabled:opacity-50 text-white font-bold text-xs shadow-md transition"
          >
            {uploading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Ingesting & Validating Statement...
              </>
            ) : (
              <>
                <UploadCloud className="w-4 h-4" /> Ingest & Validate Statement
              </>
            )}
          </button>
        </div>
      </form>

      {/* Extracted Ingestion Results & Provenance Dashboard */}
      {ingestionResult && (
        <div className="p-6 rounded-2xl bg-white/95 border border-[#2f6690]/40 shadow-md space-y-6 text-[#16425b]">
          {/* Header & Badges */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#3a7ca5]/20 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <BadgeCheck className="w-5 h-5 text-[#2f6690]" />
                <h2 className="text-base font-black text-[#16425b]">
                  Statement Successfully Ingested & Verified
                </h2>
              </div>
              <p className="text-xs text-[#2f6690]">
                Job ID: <code className="font-mono text-[#16425b] font-semibold">{ingestionResult.job_id}</code> | File: <span className="font-semibold text-[#16425b]">{ingestionResult.file_name}</span>
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#3a7ca5]/20 text-[#16425b] border border-[#3a7ca5]/40">
                Status: {ingestionResult.status}
              </span>
              {ingestionResult.completeness && (
                <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#81c3d7]/30 text-[#16425b] border border-[#81c3d7]">
                  Completeness: {ingestionResult.completeness.completeness_score_pct.toFixed(0)}%
                </span>
              )}
            </div>
          </div>

          {/* Key Financial Totals Grid */}
          {ingestionResult.financial_data && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#16425b]">
                Extracted Canonical Financial Items (PLN)
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-0.5">
                  <span className="text-3xs uppercase tracking-wider text-[#2f6690] font-semibold block">Total Revenue</span>
                  <span className="text-sm font-black text-[#16425b] font-mono">
                    {ingestionResult.financial_data.revenue != null
                      ? `PLN ${ingestionResult.financial_data.revenue.toLocaleString()}`
                      : "—"}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-0.5">
                  <span className="text-3xs uppercase tracking-wider text-[#2f6690] font-semibold block">Total Assets</span>
                  <span className="text-sm font-black text-[#16425b] font-mono">
                    {ingestionResult.financial_data.total_assets != null
                      ? `PLN ${ingestionResult.financial_data.total_assets.toLocaleString()}`
                      : "—"}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-0.5">
                  <span className="text-3xs uppercase tracking-wider text-[#2f6690] font-semibold block">Total Liabilities</span>
                  <span className="text-sm font-black text-[#16425b] font-mono">
                    {ingestionResult.financial_data.total_liabilities != null
                      ? `PLN ${ingestionResult.financial_data.total_liabilities.toLocaleString()}`
                      : "—"}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-0.5">
                  <span className="text-3xs uppercase tracking-wider text-[#2f6690] font-semibold block">Total Equity</span>
                  <span className="text-sm font-black text-[#16425b] font-mono">
                    {ingestionResult.financial_data.equity != null
                      ? `PLN ${ingestionResult.financial_data.equity.toLocaleString()}`
                      : "—"}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-0.5">
                  <span className="text-3xs uppercase tracking-wider text-[#2f6690] font-semibold block">EBITDA</span>
                  <span className="text-sm font-black text-[#2f6690] font-mono">
                    {ingestionResult.financial_data.ebitda != null
                      ? `PLN ${ingestionResult.financial_data.ebitda.toLocaleString()}`
                      : "—"}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-0.5">
                  <span className="text-3xs uppercase tracking-wider text-[#2f6690] font-semibold block">Net Profit</span>
                  <span className="text-sm font-black text-[#2f6690] font-mono">
                    {ingestionResult.financial_data.net_profit != null
                      ? `PLN ${ingestionResult.financial_data.net_profit.toLocaleString()}`
                      : "—"}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-0.5">
                  <span className="text-3xs uppercase tracking-wider text-[#2f6690] font-semibold block">Current Assets</span>
                  <span className="text-sm font-black text-[#16425b] font-mono">
                    {ingestionResult.financial_data.current_assets != null
                      ? `PLN ${ingestionResult.financial_data.current_assets.toLocaleString()}`
                      : "—"}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#d9dcd6]/40 border border-[#3a7ca5]/30 space-y-0.5">
                  <span className="text-3xs uppercase tracking-wider text-[#2f6690] font-semibold block">Working Capital</span>
                  <span className={`text-sm font-black font-mono ${
                    (ingestionResult.financial_data.working_capital ?? 0) < 0
                      ? "text-amber-700"
                      : "text-[#16425b]"
                  }`}>
                    {ingestionResult.financial_data.working_capital != null
                      ? `PLN ${ingestionResult.financial_data.working_capital.toLocaleString()}`
                      : "—"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Provenance Metadata Table */}
          <div className="p-4 rounded-xl bg-[#d9dcd6]/50 border border-[#3a7ca5]/30 space-y-2 text-xs">
            <div className="flex items-center gap-2 font-bold text-[#16425b]">
              <ShieldCheck className="w-4 h-4 text-[#2f6690]" />
              Verified Provenance Audit Trail (AGENTS.md Rule 4.3)
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-2xs text-[#2f6690] font-mono">
              <div>
                <span className="text-[#2f6690]/80 block font-sans">Source Type:</span>
                <span className="font-bold text-[#16425b]">{ingestionResult.financial_data?.source_type || "extracted_file"}</span>
              </div>
              <div>
                <span className="text-[#2f6690]/80 block font-sans">Source Reference:</span>
                <span className="font-bold text-[#16425b]">{ingestionResult.financial_data?.source_ref || ingestionResult.file_name}</span>
              </div>
              <div>
                <span className="text-[#2f6690]/80 block font-sans">Extraction Confidence:</span>
                <span className="font-bold text-[#2f6690]">{ingestionResult.financial_data?.confidence || "verified"}</span>
              </div>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <button
              type="button"
              onClick={handleReset}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl border border-[#3a7ca5]/40 hover:bg-[#d9dcd6] text-xs font-bold text-[#16425b] transition shadow-2xs"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Ingest Another Statement
            </button>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <Link
                href="/sme"
                className="w-full sm:w-auto text-center px-4 py-2 rounded-xl bg-white hover:bg-[#d9dcd6] border border-[#3a7ca5]/40 text-xs font-bold text-[#16425b] transition shadow-2xs"
              >
                View Credit Readiness
              </Link>
              <Link
                href={`/bank/assess?sme_id=${selectedSmeId}`}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2 rounded-xl bg-[#16425b] hover:bg-[#2f6690] text-xs font-bold text-white shadow-sm transition"
              >
                Assess This SME <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
      </div>
    </RoleGuard>
  );
}
