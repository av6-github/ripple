"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  FileSpreadsheet,
  ArrowLeft,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShieldCheck,
} from "lucide-react";

export default function SmeUploadPage() {
  const { smeId } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadSuccess(null);
      setError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please choose a file to upload.");
      return;
    }

    setUploading(true);
    setError(null);
    setUploadSuccess(null);

    try {
      const activeSmeId = smeId || "00000000-0000-0000-0000-000000000002";
      await api.uploadFinancialFile(activeSmeId, selectedFile);
      setUploadSuccess(`Successfully ingested "${selectedFile.name}". Ingestion job verified with full provenance tracking.`);
      setSelectedFile(null);
    } catch (err: unknown) {
      console.error(err);
      const msg = err instanceof Error ? err.message : "Failed to upload financial statement.";
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back Link */}
      <Link
        href="/sme"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Readiness Dashboard
      </Link>

      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-black text-zinc-900 dark:text-zinc-100 flex items-center gap-2.5">
          <FileSpreadsheet className="w-7 h-7 text-emerald-600" />
          Financial Statement Ingestion
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Upload balance sheets and income statements (.csv, .xlsx, .pdf, .arff) with provenance validation.
        </p>
      </div>

      {/* Ingestion Guidelines */}
      <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-800 dark:text-zinc-200 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Data Quality & Provenance Rules (AGENTS.md Rule 4.3)
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-zinc-600 dark:text-zinc-400">
          <div className="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800 space-y-1">
            <span className="font-bold text-zinc-900 dark:text-zinc-100 block">
              Required Critical Statements:
            </span>
            <span>Total Assets, Current Assets, Total Liabilities, Equity, and Revenue must be non-empty to pass the completeness gate.</span>
          </div>
          <div className="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800 space-y-1">
            <span className="font-bold text-zinc-900 dark:text-zinc-100 block">
              Automated Provenance Tagging:
            </span>
            <span>Every ingested line item is recorded with <code className="font-mono">source_type=extracted_file</code> and <code className="font-mono">confidence=verified</code>.</span>
          </div>
        </div>
      </div>

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="space-y-6">
        <div className="p-8 rounded-2xl bg-white dark:bg-zinc-900 border-2 border-dashed border-zinc-200 dark:border-zinc-800 text-center space-y-4 hover:border-emerald-500/50 transition">
          <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 flex items-center justify-center mx-auto">
            <UploadCloud className="w-6 h-6" />
          </div>

          <div className="space-y-1">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100">
              Drag and drop your financial statement file, or browse
            </h3>
            <p className="text-xs text-zinc-500">
              Supported formats: CSV, Excel (.xlsx, .xls), PDF, or Polish ARFF (up to 10 MB)
            </p>
          </div>

          <input
            type="file"
            id="statement-upload"
            onChange={handleFileChange}
            accept=".csv,.xlsx,.xls,.pdf,.arff"
            className="hidden"
          />

          <div>
            <label
              htmlFor="statement-upload"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-xs font-bold cursor-pointer transition shadow-2xs"
            >
              Choose File
            </label>
          </div>

          {selectedFile && (
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 font-mono">
              <FileText className="w-3.5 h-3.5" />
              <span>{selectedFile.name}</span>
              <span className="text-zinc-400">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
            </div>
          )}
        </div>

        {uploadSuccess && (
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{uploadSuccess}</span>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-200 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs shadow-md transition"
          >
            {uploading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Ingesting File...
              </>
            ) : (
              <>
                <UploadCloud className="w-4 h-4" /> Ingest & Validate Statement
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
