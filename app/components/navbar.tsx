"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Building2,
  ShieldCheck,
  FileSpreadsheet,
  Activity,
  LogOut,
  LogIn,
  UserPlus,
  User,
} from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, role, user, logout, setRole } = useAuth();
  const [systemReady, setSystemReady] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .checkReady()
      .then(() => setSystemReady(true))
      .catch(() => setSystemReady(false));
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const isBank = role === "bank_officer" || role === "admin";
  const isSme = role === "sme_user";

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#3a7ca5]/30 bg-[#d9dcd6]/95 backdrop-blur text-[#16425b] shadow-xs">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#16425b] text-[#81c3d7] font-black text-lg shadow-sm group-hover:bg-[#2f6690] transition">
              R
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black tracking-wider text-base text-[#16425b]">
                  RIPPLE
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-[#81c3d7]/30 text-[#16425b] font-semibold border border-[#3a7ca5]/40">
                  Prototype
                </span>
              </div>
              <p className="text-[10px] text-[#2f6690] leading-tight font-medium">
                Explainable SME Credit Risk
              </p>
            </div>
          </Link>

          {/* Navigation Links — Strict Profile Segregation */}
          <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
            {!isAuthenticated ? (
              <Link
                href="/"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                  pathname === "/"
                    ? "bg-[#3a7ca5]/25 text-[#16425b] font-bold border border-[#3a7ca5]/40 shadow-2xs"
                    : "text-[#2f6690] hover:text-[#16425b] hover:bg-[#3a7ca5]/10"
                }`}
              >
                Overview
              </Link>
            ) : isBank ? (
              <>
                <Link
                  href="/bank"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                    pathname === "/bank"
                      ? "bg-[#3a7ca5]/25 text-[#16425b] font-bold border border-[#3a7ca5]/40 shadow-2xs"
                      : "text-[#2f6690] hover:text-[#16425b] hover:bg-[#3a7ca5]/10"
                  }`}
                >
                  <Building2 className="w-4 h-4 text-[#3a7ca5]" />
                  Portfolio Dashboard
                </Link>
                <Link
                  href="/bank/assess"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                    pathname.startsWith("/bank/assess")
                      ? "bg-[#3a7ca5]/25 text-[#16425b] font-bold border border-[#3a7ca5]/40 shadow-2xs"
                      : "text-[#2f6690] hover:text-[#16425b] hover:bg-[#3a7ca5]/10"
                  }`}
                >
                  <Activity className="w-4 h-4 text-[#3a7ca5]" />
                  Assessment Wizard
                </Link>
              </>
            ) : isSme ? (
              <>
                <Link
                  href="/sme"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                    pathname === "/sme"
                      ? "bg-[#3a7ca5]/25 text-[#16425b] font-bold border border-[#3a7ca5]/40 shadow-2xs"
                      : "text-[#2f6690] hover:text-[#16425b] hover:bg-[#3a7ca5]/10"
                  }`}
                >
                  <ShieldCheck className="w-4 h-4 text-[#2f6690]" />
                  Credit Readiness
                </Link>
                <Link
                  href="/sme/upload"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                    pathname === "/sme/upload"
                      ? "bg-[#3a7ca5]/25 text-[#16425b] font-bold border border-[#3a7ca5]/40 shadow-2xs"
                      : "text-[#2f6690] hover:text-[#16425b] hover:bg-[#3a7ca5]/10"
                  }`}
                >
                  <FileSpreadsheet className="w-4 h-4 text-[#2f6690]" />
                  Upload Statements
                </Link>
              </>
            ) : null}
          </nav>
        </div>

        {/* Right Controls: Health & Auth State */}
        <div className="flex items-center gap-3">
          {/* Readiness Health Indicator */}
          <div
            title={
              systemReady === true
                ? "Remote PostgreSQL, Neo4j & ML Engine connected"
                : systemReady === false
                ? "Backend services offline or starting up"
                : "Checking backend readiness..."
            }
            className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-mono border border-[#3a7ca5]/30 bg-white/70 shadow-2xs text-[#16425b]"
          >
            {systemReady === true ? (
              <>
                <span className="w-2 h-2 rounded-full bg-[#2f6690]"></span>
                <span className="text-[#16425b] font-semibold">Backend Ready</span>
              </>
            ) : systemReady === false ? (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                <span className="text-[#16425b]">Offline</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-[#3a7ca5] animate-pulse"></span>
                <span className="text-[#2f6690]">Connecting</span>
              </>
            )}
          </div>

          {/* Authenticated User / Guest Controls */}
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg border border-[#3a7ca5]/40 bg-white/60">
                <div
                  className={`p-1 rounded ${
                    isBank ? "bg-[#16425b] text-[#81c3d7]" : "bg-[#2f6690] text-[#d9dcd6]"
                  }`}
                >
                  {isBank ? (
                    <Building2 className="w-3.5 h-3.5" />
                  ) : (
                    <ShieldCheck className="w-3.5 h-3.5" />
                  )}
                </div>
                <div className="text-left">
                  <p className="text-[11px] font-bold text-[#16425b] leading-tight line-clamp-1">
                    {user.first_name
                      ? `${user.first_name} ${user.last_name || ""}`
                      : user.email}
                  </p>
                  <p className="text-[10px] text-[#2f6690] leading-tight font-mono">
                    {isBank ? "Bank Credit Officer" : user.organization || "SME Borrower"}
                  </p>
                </div>
              </div>

              <button
                onClick={() => {
                  if (isBank) {
                    setRole("sme_user");
                    router.push("/sme");
                  } else {
                    setRole("bank_officer");
                    router.push("/bank");
                  }
                }}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-bold rounded-lg border border-[#3a7ca5]/40 text-[#16425b] bg-white/80 hover:bg-[#81c3d7]/25 transition shadow-2xs"
                title={isBank ? "Switch to SME Borrower Portal" : "Switch to Bank Credit Officer Console"}
              >
                {isBank ? (
                  <>
                    <ShieldCheck className="w-3.5 h-3.5 text-[#2f6690]" />
                    <span className="hidden md:inline">SME Portal</span>
                  </>
                ) : (
                  <>
                    <Building2 className="w-3.5 h-3.5 text-[#2f6690]" />
                    <span className="hidden md:inline">Bank Console</span>
                  </>
                )}
              </button>

              <button
                onClick={handleLogout}
                title="Reset session"
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-md border border-[#3a7ca5]/40 text-[#16425b] hover:bg-[#d9dcd6] transition cursor-pointer shadow-2xs"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Reset</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-[#2f6690] text-[#d9dcd6] hover:bg-[#16425b] transition shadow-xs"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
              <Link
                href="/register"
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg border border-[#3a7ca5]/40 text-[#16425b] hover:bg-[#3a7ca5]/15 transition shadow-2xs"
              >
                <UserPlus className="w-3.5 h-3.5 text-[#2f6690]" />
                <span>Register</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
