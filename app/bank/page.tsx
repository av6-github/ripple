"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { SmeProfile } from "@/lib/types";
import { SyntheticBadge } from "@/app/components/badges";
import {
  Building2,
  Search,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  Briefcase,
  AlertCircle,
  RefreshCw,
} from "lucide-react";

export default function BankDashboardPage() {
  const [smes, setSmes] = useState<SmeProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSector, setSelectedSector] = useState<string>("ALL");

  const fetchSmes = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listSmes();
      setSmes(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      console.error(err);
      const msg = err instanceof Error ? err.message : "Failed to load SME portfolio from remote backend.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    api
      .listSmes()
      .then((data) => {
        if (active) setSmes(Array.isArray(data) ? data : []);
      })
      .catch((err: unknown) => {
        if (active) {
          const msg = err instanceof Error ? err.message : "Failed to load SME portfolio from remote backend.";
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

  const sectors = ["ALL", ...Array.from(new Set(smes.map((s) => s.sector || s.industry || "General")))];

  const filtered = smes.filter((s) => {
    const matchesSearch =
      s.legal_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.tax_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector =
      selectedSector === "ALL" || (s.sector || s.industry || "General") === selectedSector;
    return matchesSearch && matchesSector;
  });

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-zinc-900 dark:text-zinc-100 flex items-center gap-2.5">
            <Building2 className="w-7 h-7 text-indigo-600" />
            SME Credit Risk Portfolio
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Bank Officer Decision Support Console · Remote Persistence (PostgreSQL & Neo4j)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchSmes}
            className="p-2 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-850 text-zinc-600 dark:text-zinc-300 transition"
            title="Refresh portfolio"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Link
            href="/bank/assess"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-xs transition"
          >
            <PlusCircle className="w-4 h-4" />
            New SME Assessment
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            Total Monitored SMEs
          </div>
          <div className="text-3xl font-black text-zinc-900 dark:text-zinc-100 mt-1">
            {smes.length}
          </div>
          <p className="text-xs text-zinc-500 mt-1">Registered borrower profiles</p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            Active Sectors
          </div>
          <div className="text-3xl font-black text-indigo-600 dark:text-indigo-400 mt-1">
            {sectors.length - 1}
          </div>
          <p className="text-xs text-zinc-500 mt-1">Industry classifications</p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            Decision Framework
          </div>
          <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-2 flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4" />
            Officer Custody (Rule 4.6)
          </div>
          <p className="text-xs text-zinc-500 mt-1">Human officer decision authority</p>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by legal name or tax ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 text-zinc-900 dark:text-zinc-100"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <span className="text-xs font-semibold text-zinc-500 whitespace-nowrap">Sector:</span>
          {sectors.map((sec) => (
            <button
              key={sec}
              onClick={() => setSelectedSector(sec)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition whitespace-nowrap ${
                selectedSector === sec
                  ? "bg-indigo-600 text-white font-bold"
                  : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200"
              }`}
            >
              {sec}
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-rose-900 dark:text-rose-200">
              Connection to Backend Error
            </h4>
            <p className="text-xs text-rose-700 dark:text-rose-300">{error}</p>
            <p className="text-xs text-rose-600 dark:text-rose-400">
              Ensure FastAPI backend is running at <code className="font-mono">http://localhost:8000</code>.
            </p>
          </div>
        </div>
      )}

      {/* SME Table */}
      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center space-y-3">
            <RefreshCw className="w-6 h-6 text-indigo-600 animate-spin mx-auto" />
            <p className="text-sm text-zinc-500 font-medium">Loading portfolio records...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Briefcase className="w-8 h-8 text-zinc-400 mx-auto" />
            <h3 className="text-base font-bold text-zinc-700 dark:text-zinc-300">
              No SME Profiles Found
            </h3>
            <p className="text-xs text-zinc-500 max-w-sm mx-auto">
              No businesses matched your search query or portfolio is empty. Launch the assessment wizard to create a new evaluation.
            </p>
            <Link
              href="/bank/assess"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold mt-2 shadow-xs"
            >
              <PlusCircle className="w-3.5 h-3.5" /> Start Assessment
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/50 text-xs font-bold uppercase tracking-wider text-zinc-500">
                <tr>
                  <th className="py-3.5 px-4">Legal Business Name</th>
                  <th className="py-3.5 px-4">Tax Identifier</th>
                  <th className="py-3.5 px-4">Sector</th>
                  <th className="py-3.5 px-4">Synthetic Flag</th>
                  <th className="py-3.5 px-4">Created Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {filtered.map((sme) => (
                  <tr
                    key={sme.id}
                    className="hover:bg-zinc-50/70 dark:hover:bg-zinc-850/40 transition group"
                  >
                    <td className="py-3.5 px-4 font-semibold text-zinc-900 dark:text-zinc-100">
                      {sme.legal_name}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-zinc-600 dark:text-zinc-400">
                      {sme.tax_id}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-700">
                        {sme.sector || sme.industry || "General"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      {sme.is_synthetic ? (
                        <SyntheticBadge isSynthetic={true} />
                      ) : (
                        <span className="text-xs text-zinc-400 font-mono">Real-World</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-zinc-500 font-mono">
                      {new Date(sme.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/bank/smes/${sme.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 group-hover:underline"
                      >
                        Profile & History
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
