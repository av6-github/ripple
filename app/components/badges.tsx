import React from "react";
import { Recommendation, RiskBand } from "@/lib/types";

export function RiskBandBadge({ band }: { band: RiskBand | string }) {
  const norm = band.toUpperCase();
  let color = "bg-zinc-100 text-zinc-700 border-zinc-300 dark:bg-zinc-800 dark:text-zinc-300";

  if (norm.includes("BAND A") || norm === "LOW") {
    color = "bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800";
  } else if (norm.includes("BAND B") || norm === "MEDIUM_LOW") {
    color = "bg-blue-50 text-blue-700 border-blue-300 dark:bg-blue-950/50 dark:text-blue-300 dark:border-blue-800";
  } else if (norm.includes("BAND C") || norm === "MEDIUM_HIGH") {
    color = "bg-amber-50 text-amber-700 border-amber-300 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800";
  } else if (norm.includes("BAND D") || norm === "HIGH" || norm === "VERY_HIGH") {
    color = "bg-rose-50 text-rose-700 border-rose-300 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800";
  } else if (norm.includes("INCONCLUSIVE")) {
    color = "bg-[#3a7ca5]/15 text-[#16425b] border-[#3a7ca5]/40";
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${color}`}
    >
      {band}
    </span>
  );
}

export function RecommendationBadge({ rec }: { rec: Recommendation | string }) {
  const norm = rec.toUpperCase();
  let color = "bg-zinc-100 text-zinc-700 border-zinc-300";
  let label = rec;

  if (norm === "LOWER_RISK") {
    color = "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/60 dark:text-emerald-200";
    label = "Lower Risk (Standard Terms)";
  } else if (norm === "FURTHER_REVIEW") {
    color = "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-900/60 dark:text-amber-200";
    label = "Further Review (Committee)";
  } else if (norm === "HIGHER_RISK") {
    color = "bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-900/60 dark:text-rose-200";
    label = "Higher Risk (Elevated Hazard)";
  } else if (norm === "INCONCLUSIVE") {
    color = "bg-[#3a7ca5]/20 text-[#16425b] border-[#3a7ca5]/50";
    label = "Inconclusive (Data Missing)";
  }

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider border ${color}`}
    >
      {label}
    </span>
  );
}

export function SyntheticBadge({ isSynthetic = true }: { isSynthetic?: boolean }) {
  if (!isSynthetic) return null;
  return (
    <span
      title="AGENTS.md Rule 4.4: Synthetic commercial relationship"
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-500/10 text-amber-600 border border-amber-500/30 dark:text-amber-400"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
      is_synthetic = true
    </span>
  );
}

export function ProvenanceBadge({
  sourceType,
  confidence,
}: {
  sourceType?: string;
  confidence?: string;
}) {
  return (
    <div className="inline-flex items-center gap-1.5 text-xs text-zinc-500 font-mono">
      <span className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
        src: {sourceType || "extracted_file"}
      </span>
      <span className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-emerald-600 dark:text-emerald-400">
        conf: {confidence || "verified"}
      </span>
    </div>
  );
}
