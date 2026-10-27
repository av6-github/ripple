"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { SmeProfile, LoanApplicationRecord, CreateLoanApplicationRequest } from "@/lib/types";
import { SyntheticBadge } from "@/app/components/badges";
import { RoleGuard } from "@/app/components/RoleGuard";
import {
  Building2,
  Search,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  Briefcase,
  AlertCircle,
  RefreshCw,
  FileText,
  Clock,
  CheckCircle2,
  DollarSign,
  Calendar,
  X,
  FileCheck2,
} from "lucide-react";

export default function BankDashboardPage() {
  const [activeTab, setActiveTab] = useState<"applications" | "portfolio">("applications");
  const [smes, setSmes] = useState<SmeProfile[]>([]);
  const [applications, setApplications] = useState<LoanApplicationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSector, setSelectedSector] = useState<string>("ALL");
  const [selectedAppStatus, setSelectedAppStatus] = useState<string>("ALL");

  // New Loan Intake Modal
  const [showIntakeModal, setShowIntakeModal] = useState(false);
  const [submittingIntake, setSubmittingIntake] = useState(false);
  const [intakeError, setIntakeError] = useState<string | null>(null);
  const [intakeSuccess, setIntakeSuccess] = useState<string | null>(null);
  const [intakeForm, setIntakeForm] = useState<CreateLoanApplicationRequest>({
    sme_id: "",
    facility_type: "WORKING_CAPITAL_REVOLVER",
    requested_amount: 500000,
    tenor_months: 24,
    purpose: "Working capital expansion and inventory pre-financing",
    self_reported_revenue: 1450000,
    self_reported_assets: 980000,
    self_reported_liabilities: 490000,
    self_reported_equity: 490000,
    self_reported_net_profit: 72000,
    self_reported_cash: 65000,
    contact_name: "Tomasz Nowak",
    contact_email: "t.nowak@enterprise.pl",
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [smeList, appList] = await Promise.all([
        api.listSmes(),
        api.listLoanApplications(),
      ]);
      setSmes(Array.isArray(smeList) ? smeList : []);
      setApplications(Array.isArray(appList) ? appList : []);
      if (smeList.length > 0 && !intakeForm.sme_id) {
        setIntakeForm((prev) => ({ ...prev, sme_id: smeList[0].id }));
      }
    } catch (err: unknown) {
      console.error(err);
      const msg = err instanceof Error ? err.message : "Failed to load records from remote backend.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateIntake = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!intakeForm.sme_id) {
      setIntakeError("Please select an SME borrower.");
      return;
    }
    setSubmittingIntake(true);
    setIntakeError(null);
    try {
      await api.createLoanApplication(intakeForm);
      setIntakeSuccess("Loan intake recorded successfully.");
      setTimeout(() => {
        setIntakeSuccess(null);
        setShowIntakeModal(false);
      }, 1000);
      // Refresh list
      const updatedApps = await api.listLoanApplications();
      setApplications(Array.isArray(updatedApps) ? updatedApps : []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to record loan intake.";
      setIntakeError(msg);
    } finally {
      setSubmittingIntake(false);
    }
  };

  const sectors = ["ALL", ...Array.from(new Set(smes.map((s) => s.sector || s.industry || "General")))];

  // Filtered applications
  const filteredApps = applications.filter((app) => {
    const matchesSearch =
      (app.legal_name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (app.tax_id || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (app.purpose || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (app.facility_type || "").toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      selectedAppStatus === "ALL" || app.status === selectedAppStatus;
    return matchesSearch && matchesStatus;
  });

  // Filtered SMEs
  const filteredSmes = smes.filter((s) => {
    const matchesSearch =
      s.legal_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.tax_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector =
      selectedSector === "ALL" || (s.sector || s.industry || "General") === selectedSector;
    return matchesSearch && matchesSector;
  });

  const pendingAppsCount = applications.filter((a) => a.status === "PENDING_REVIEW").length;

  return (
    <RoleGuard allowedRoles={["bank_officer", "admin"]}>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-8 text-[#16425b]">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-[#16425b] flex items-center gap-2.5">
              <Building2 className="w-7 h-7 text-[#2f6690]" />
              SME Credit Risk Console
            </h1>
            <p className="text-sm text-[#2f6690]">
              Bank Officer Decision Support & Underwriting Queue · Remote Persistence (Supabase & Neo4j)
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              className="p-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white/70 hover:bg-[#d9dcd6] text-[#16425b] transition shadow-2xs"
              title="Refresh console"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={() => setShowIntakeModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[#2f6690] bg-white hover:bg-[#81c3d7]/20 text-[#2f6690] font-bold text-sm shadow-xs transition"
            >
              <FileCheck2 className="w-4 h-4" />
              New Loan Intake
            </button>
            <Link
              href="/bank/assess"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2f6690] hover:bg-[#16425b] text-white font-bold text-sm shadow-md transition"
            >
              <PlusCircle className="w-4 h-4" />
              New SME Assessment
            </Link>
          </div>
        </div>

        {/* KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs">
            <div className="text-xs font-semibold text-[#2f6690] uppercase tracking-wider">
              Pending Applications
            </div>
            <div className="text-3xl font-black text-amber-600 mt-1">
              {pendingAppsCount}
            </div>
            <p className="text-xs text-[#2f6690] mt-1">Awaiting credit assessment</p>
          </div>

          <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs">
            <div className="text-xs font-semibold text-[#2f6690] uppercase tracking-wider">
              Total Applications
            </div>
            <div className="text-3xl font-black text-[#16425b] mt-1">
              {applications.length}
            </div>
            <p className="text-xs text-[#2f6690] mt-1">Incoming facility requests</p>
          </div>

          <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs">
            <div className="text-xs font-semibold text-[#2f6690] uppercase tracking-wider">
              Monitored SMEs
            </div>
            <div className="text-3xl font-black text-[#2f6690] mt-1">
              {smes.length}
            </div>
            <p className="text-xs text-[#2f6690] mt-1">Active enterprise profiles</p>
          </div>

          <div className="p-5 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs">
            <div className="text-xs font-semibold text-[#2f6690] uppercase tracking-wider">
              Underwriting Standard
            </div>
            <div className="text-sm font-bold text-[#2f6690] mt-2 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-[#16425b]" />
              Officer Custody (Rule 4.6)
            </div>
            <p className="text-xs text-[#2f6690] mt-1">Human officer decision authority</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-[#3a7ca5]/30 pb-2">
          <button
            onClick={() => setActiveTab("applications")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition ${
              activeTab === "applications"
                ? "bg-[#16425b] text-white shadow-xs"
                : "text-[#2f6690] hover:bg-white/60"
            }`}
          >
            <FileText className="w-4 h-4" />
            Loan Applications Queue
            {pendingAppsCount > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs bg-amber-500 text-white font-mono">
                {pendingAppsCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("portfolio")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition ${
              activeTab === "portfolio"
                ? "bg-[#16425b] text-white shadow-xs"
                : "text-[#2f6690] hover:bg-white/60"
            }`}
          >
            <Building2 className="w-4 h-4" />
            SME Portfolio Directory
            <span className="px-2 py-0.5 rounded-full text-xs bg-[#2f6690]/20 text-[#16425b] font-mono">
              {smes.length}
            </span>
          </button>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-300 flex items-start gap-3 shadow-xs">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-rose-950">
                Connection to Backend Error
              </h4>
              <p className="text-xs text-rose-800">{error}</p>
              <p className="text-xs text-rose-700">
                Ensure FastAPI backend is running at <code className="font-mono bg-white px-1 py-0.5 rounded border border-rose-300">http://localhost:8000</code>.
              </p>
            </div>
          </div>
        )}

        {/* TAB 1: APPLICATIONS QUEUE */}
        {activeTab === "applications" && (
          <div className="space-y-6">
            {/* Filters Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs">
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 text-[#2f6690] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search application by company or purpose..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-[#3a7ca5]/40 bg-white text-[#16425b] placeholder-[#2f6690]/60 focus:outline-none focus:ring-2 focus:ring-[#3a7ca5]"
                />
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
                <span className="text-xs font-bold text-[#16425b] whitespace-nowrap">Status:</span>
                {["ALL", "PENDING_REVIEW", "ASSESSED", "APPROVED"].map((status) => (
                  <button
                    key={status}
                    onClick={() => setSelectedAppStatus(status)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                      selectedAppStatus === status
                        ? "bg-[#16425b] text-white shadow-xs"
                        : "bg-white border border-[#3a7ca5]/30 text-[#2f6690] hover:bg-[#d9dcd6]"
                    }`}
                  >
                    {status.replace(/_/g, " ")}
                  </button>
                ))}
              </div>
            </div>

            {/* Applications List */}
            {loading ? (
              <div className="p-12 text-center space-y-3 bg-white/90 rounded-2xl border border-[#3a7ca5]/30">
                <RefreshCw className="w-6 h-6 text-[#2f6690] animate-spin mx-auto" />
                <p className="text-sm text-[#2f6690] font-medium">Loading loan applications...</p>
              </div>
            ) : filteredApps.length === 0 ? (
              <div className="p-12 text-center space-y-3 bg-white/90 rounded-2xl border border-[#3a7ca5]/30">
                <Briefcase className="w-8 h-8 text-[#2f6690]/60 mx-auto" />
                <h3 className="text-base font-bold text-[#16425b]">No Applications Found</h3>
                <p className="text-xs text-[#2f6690] max-w-sm mx-auto">
                  No loan facility applications match your criteria. You can record a new application on behalf of an SME.
                </p>
                <button
                  onClick={() => setShowIntakeModal(true)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#2f6690] hover:bg-[#16425b] text-white text-xs font-bold mt-2 shadow-xs transition"
                >
                  <PlusCircle className="w-3.5 h-3.5" /> Record Loan Intake
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {filteredApps.map((app) => (
                  <div
                    key={app.id}
                    className="p-5 rounded-2xl bg-white/95 border border-[#3a7ca5]/30 hover:border-[#3a7ca5] shadow-xs transition space-y-4"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#3a7ca5]/15 pb-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-bold text-[#16425b]">
                            {app.legal_name || "Applicant SME"}
                          </h3>
                          <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#81c3d7]/20 text-[#16425b] border border-[#3a7ca5]/30">
                            NIP: {app.tax_id || "N/A"}
                          </span>
                          <span className="text-xs text-[#2f6690]">
                            {app.city || app.sector || "Poland"}
                          </span>
                        </div>
                        <p className="text-xs text-[#2f6690]">
                          Purpose: <span className="text-[#16425b] font-medium">{app.purpose}</span>
                        </p>
                      </div>

                      <div className="flex items-center gap-2 self-start sm:self-auto">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-bold border ${
                            app.status === "PENDING_REVIEW"
                              ? "bg-amber-100 text-amber-800 border-amber-300"
                              : app.status === "ASSESSED"
                              ? "bg-blue-100 text-blue-800 border-blue-300"
                              : "bg-emerald-100 text-emerald-800 border-emerald-300"
                          }`}
                        >
                          {app.status.replace(/_/g, " ")}
                        </span>
                      </div>
                    </div>

                    {/* Facility & Self-Reported Metrics Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs bg-[#d9dcd6]/20 p-3.5 rounded-xl border border-[#3a7ca5]/20 font-mono">
                      <div>
                        <span className="text-[#2f6690] block text-[10px] font-sans uppercase font-bold">
                          Facility Type
                        </span>
                        <strong className="text-[#16425b] text-xs">
                          {app.facility_type.replace(/_/g, " ")}
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#2f6690] block text-[10px] font-sans uppercase font-bold">
                          Requested Amount
                        </span>
                        <strong className="text-emerald-800 text-sm">
                          {app.requested_amount.toLocaleString()} PLN
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#2f6690] block text-[10px] font-sans uppercase font-bold">
                          Tenor
                        </span>
                        <strong className="text-[#16425b] text-xs">
                          {app.tenor_months} months
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#2f6690] block text-[10px] font-sans uppercase font-bold">
                          Self-Reported Rev
                        </span>
                        <strong className="text-[#16425b] text-xs">
                          {app.self_reported_revenue?.toLocaleString()} PLN
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#2f6690] block text-[10px] font-sans uppercase font-bold">
                          Self-Reported Net Profit
                        </span>
                        <strong className="text-[#16425b] text-xs">
                          {app.self_reported_net_profit?.toLocaleString()} PLN
                        </strong>
                      </div>
                    </div>

                    {/* Actions footer */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                      <div className="text-[11px] text-[#2f6690]">
                        Submitted: {new Date(app.created_at).toLocaleDateString()} {new Date(app.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        {app.contact_name && ` · Contact: ${app.contact_name} (${app.contact_email || ""})`}
                      </div>

                      <div className="flex items-center gap-2">
                        {app.assessment_id && (
                          <Link
                            href={`/bank/assessments/${app.assessment_id}`}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#3a7ca5]/40 bg-white hover:bg-[#81c3d7]/20 text-[#2f6690] text-xs font-bold transition shadow-2xs"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                            View Assessment
                          </Link>
                        )}
                        <Link
                          href={`/bank/assess?application_id=${app.id}`}
                          className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-[#2f6690] hover:bg-[#16425b] text-white text-xs font-bold transition shadow-xs"
                        >
                          {app.status === "PENDING_REVIEW" ? "Assess Application" : "Re-Assess"}
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: SME PORTFOLIO */}
        {activeTab === "portfolio" && (
          <div className="space-y-6">
            {/* Filters & Search */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-white/90 border border-[#3a7ca5]/30 shadow-xs">
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 text-[#2f6690] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by legal name or tax ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-[#3a7ca5]/40 bg-white text-[#16425b] placeholder-[#2f6690]/60 focus:outline-none focus:ring-2 focus:ring-[#3a7ca5]"
                />
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
                <span className="text-xs font-bold text-[#16425b] whitespace-nowrap">Sector:</span>
                {sectors.map((sec) => (
                  <button
                    key={sec}
                    onClick={() => setSelectedSector(sec)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                      selectedSector === sec
                        ? "bg-[#16425b] text-white shadow-xs"
                        : "bg-white border border-[#3a7ca5]/30 text-[#2f6690] hover:bg-[#d9dcd6]"
                    }`}
                  >
                    {sec}
                  </button>
                ))}
              </div>
            </div>

            {/* SME Table */}
            <div className="rounded-2xl border border-[#3a7ca5]/30 bg-white/90 shadow-xs overflow-hidden">
              {loading ? (
                <div className="p-12 text-center space-y-3">
                  <RefreshCw className="w-6 h-6 text-[#2f6690] animate-spin mx-auto" />
                  <p className="text-sm text-[#2f6690] font-medium">Loading portfolio records...</p>
                </div>
              ) : filteredSmes.length === 0 ? (
                <div className="p-12 text-center space-y-3">
                  <Briefcase className="w-8 h-8 text-[#2f6690]/60 mx-auto" />
                  <h3 className="text-base font-bold text-[#16425b]">
                    No SME Profiles Found
                  </h3>
                  <p className="text-xs text-[#2f6690] max-w-sm mx-auto">
                    No businesses matched your search query. Launch the assessment wizard to create a new evaluation.
                  </p>
                  <Link
                    href="/bank/assess"
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#2f6690] hover:bg-[#16425b] text-white text-xs font-bold mt-2 shadow-xs transition"
                  >
                    <PlusCircle className="w-3.5 h-3.5" /> Start Assessment
                  </Link>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-[#3a7ca5]/30 bg-[#3a7ca5]/10 text-xs font-bold uppercase tracking-wider text-[#16425b]">
                      <tr>
                        <th className="py-3.5 px-4">Legal Business Name</th>
                        <th className="py-3.5 px-4">Tax Identifier</th>
                        <th className="py-3.5 px-4">Sector</th>
                        <th className="py-3.5 px-4">Synthetic Flag</th>
                        <th className="py-3.5 px-4">Created Date</th>
                        <th className="py-3.5 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#3a7ca5]/20">
                      {filteredSmes.map((sme) => (
                        <tr
                          key={sme.id}
                          className="hover:bg-[#81c3d7]/15 transition group"
                        >
                          <td className="py-3.5 px-4 font-bold text-[#16425b]">
                            {sme.legal_name}
                          </td>
                          <td className="py-3.5 px-4 font-mono text-xs text-[#2f6690]">
                            {sme.tax_id}
                          </td>
                          <td className="py-3.5 px-4">
                            <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-semibold bg-[#81c3d7]/30 text-[#16425b] border border-[#3a7ca5]/30">
                              {sme.sector || sme.industry || "General"}
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            {sme.is_synthetic ? (
                              <SyntheticBadge isSynthetic={true} />
                            ) : (
                              <span className="text-xs text-[#2f6690] font-mono">Real-World</span>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-xs text-[#2f6690] font-mono">
                            {new Date(sme.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <Link
                              href={`/bank/smes/${sme.id}`}
                              className="inline-flex items-center gap-1 text-xs font-bold text-[#2f6690] hover:text-[#16425b] group-hover:underline"
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
        )}

        {/* MODAL: Record New Loan Intake */}
        {showIntakeModal && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-white rounded-3xl border border-[#3a7ca5]/40 shadow-2xl max-w-2xl w-full p-6 space-y-6 text-[#16425b] my-8 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-[#3a7ca5]/20 pb-4">
                <div className="space-y-1">
                  <h3 className="text-lg font-bold text-[#16425b] flex items-center gap-2">
                    <FileCheck2 className="w-5 h-5 text-[#2f6690]" />
                    Record Loan Application Intake
                  </h3>
                  <p className="text-xs text-[#2f6690]">
                    Log a credit facility application on behalf of a portfolio SME.
                  </p>
                </div>
                <button
                  onClick={() => setShowIntakeModal(false)}
                  className="p-1 rounded-lg hover:bg-[#d9dcd6] text-[#2f6690]"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {intakeError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-300 text-xs text-rose-800">
                  {intakeError}
                </div>
              )}

              {intakeSuccess && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-300 text-xs text-emerald-800">
                  {intakeSuccess}
                </div>
              )}

              <form onSubmit={handleCreateIntake} className="space-y-4">
                {/* Target SME */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#2f6690] mb-1">
                    Select Borrower SME
                  </label>
                  <select
                    value={intakeForm.sme_id}
                    onChange={(e) => setIntakeForm({ ...intakeForm, sme_id: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-sm text-[#16425b] font-medium"
                    required
                  >
                    {smes.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.legal_name} (NIP: {s.tax_id})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#2f6690] mb-1">
                      Facility Type
                    </label>
                    <select
                      value={intakeForm.facility_type}
                      onChange={(e) => setIntakeForm({ ...intakeForm, facility_type: e.target.value })}
                      className="w-full p-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-sm text-[#16425b]"
                    >
                      <option value="WORKING_CAPITAL_REVOLVER">Working Capital Revolver</option>
                      <option value="TERM_LOAN">Term Loan</option>
                      <option value="EQUIPMENT_FINANCING">Equipment / Capex Financing</option>
                      <option value="INVOICE_DISCOUNTING">Trade / Invoice Discounting</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#2f6690] mb-1">
                      Requested Amount (PLN)
                    </label>
                    <input
                      type="number"
                      value={intakeForm.requested_amount}
                      onChange={(e) => setIntakeForm({ ...intakeForm, requested_amount: parseFloat(e.target.value) || 0 })}
                      className="w-full p-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-sm font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#2f6690] mb-1">
                      Tenor (Months)
                    </label>
                    <input
                      type="number"
                      value={intakeForm.tenor_months}
                      onChange={(e) => setIntakeForm({ ...intakeForm, tenor_months: parseInt(e.target.value) || 12 })}
                      className="w-full p-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-sm font-mono"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#2f6690] mb-1">
                      Business Purpose
                    </label>
                    <input
                      type="text"
                      value={intakeForm.purpose}
                      onChange={(e) => setIntakeForm({ ...intakeForm, purpose: e.target.value })}
                      className="w-full p-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-sm"
                      placeholder="e.g. Working capital expansion"
                      required
                    />
                  </div>
                </div>

                {/* Self-Reported Metrics Section */}
                <div className="p-4 rounded-2xl bg-[#d9dcd6]/25 border border-[#3a7ca5]/30 space-y-3">
                  <div className="text-xs font-bold text-[#16425b] uppercase tracking-wider flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-[#2f6690]" />
                    Borrower Self-Reported Financial Statement (Source A)
                  </div>
                  <p className="text-[11px] text-[#2f6690]">
                    These figures will populate Dual-Source Reconciliation and be cross-checked against KRS / VAT records.
                  </p>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono text-xs">
                    <div>
                      <label className="block text-[10px] uppercase font-sans font-bold text-[#2f6690] mb-0.5">
                        Revenue (PLN)
                      </label>
                      <input
                        type="number"
                        value={intakeForm.self_reported_revenue}
                        onChange={(e) => setIntakeForm({ ...intakeForm, self_reported_revenue: parseFloat(e.target.value) || 0 })}
                        className="w-full p-2 rounded-lg border border-[#3a7ca5]/40 bg-white text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] uppercase font-sans font-bold text-[#2f6690] mb-0.5">
                        Total Assets (PLN)
                      </label>
                      <input
                        type="number"
                        value={intakeForm.self_reported_assets}
                        onChange={(e) => setIntakeForm({ ...intakeForm, self_reported_assets: parseFloat(e.target.value) || 0 })}
                        className="w-full p-2 rounded-lg border border-[#3a7ca5]/40 bg-white text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] uppercase font-sans font-bold text-[#2f6690] mb-0.5">
                        Total Liabilities (PLN)
                      </label>
                      <input
                        type="number"
                        value={intakeForm.self_reported_liabilities}
                        onChange={(e) => setIntakeForm({ ...intakeForm, self_reported_liabilities: parseFloat(e.target.value) || 0 })}
                        className="w-full p-2 rounded-lg border border-[#3a7ca5]/40 bg-white text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] uppercase font-sans font-bold text-[#2f6690] mb-0.5">
                        Total Equity (PLN)
                      </label>
                      <input
                        type="number"
                        value={intakeForm.self_reported_equity}
                        onChange={(e) => setIntakeForm({ ...intakeForm, self_reported_equity: parseFloat(e.target.value) || 0 })}
                        className="w-full p-2 rounded-lg border border-[#3a7ca5]/40 bg-white text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] uppercase font-sans font-bold text-[#2f6690] mb-0.5">
                        Net Profit (PLN)
                      </label>
                      <input
                        type="number"
                        value={intakeForm.self_reported_net_profit}
                        onChange={(e) => setIntakeForm({ ...intakeForm, self_reported_net_profit: parseFloat(e.target.value) || 0 })}
                        className="w-full p-2 rounded-lg border border-[#3a7ca5]/40 bg-white text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] uppercase font-sans font-bold text-[#2f6690] mb-0.5">
                        Cash & Equiv (PLN)
                      </label>
                      <input
                        type="number"
                        value={intakeForm.self_reported_cash}
                        onChange={(e) => setIntakeForm({ ...intakeForm, self_reported_cash: parseFloat(e.target.value) || 0 })}
                        className="w-full p-2 rounded-lg border border-[#3a7ca5]/40 bg-white text-xs"
                      />
                    </div>
                  </div>
                </div>

                {/* Contact details */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#2f6690] mb-1">
                      Applicant Contact Name
                    </label>
                    <input
                      type="text"
                      value={intakeForm.contact_name || ""}
                      onChange={(e) => setIntakeForm({ ...intakeForm, contact_name: e.target.value })}
                      className="w-full p-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#2f6690] mb-1">
                      Applicant Email
                    </label>
                    <input
                      type="email"
                      value={intakeForm.contact_email || ""}
                      onChange={(e) => setIntakeForm({ ...intakeForm, contact_email: e.target.value })}
                      className="w-full p-2.5 rounded-xl border border-[#3a7ca5]/40 bg-white text-sm"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#3a7ca5]/20">
                  <button
                    type="button"
                    onClick={() => setShowIntakeModal(false)}
                    className="px-4 py-2.5 rounded-xl border border-[#3a7ca5]/40 text-xs font-bold text-[#2f6690] hover:bg-[#d9dcd6]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingIntake}
                    className="px-5 py-2.5 rounded-xl bg-[#2f6690] hover:bg-[#16425b] text-white text-xs font-bold transition shadow-xs disabled:opacity-50 flex items-center gap-2"
                  >
                    {submittingIntake ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4" />
                    )}
                    Record Application Intake
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}
