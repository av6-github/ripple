"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Building2,
  ShieldCheck,
  FileSpreadsheet,
  Activity,
  Users,
} from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const { role, setRole } = useAuth();
  const [systemReady, setSystemReady] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .checkReady()
      .then(() => setSystemReady(true))
      .catch(() => setSystemReady(false));
  }, []);

  const isBank = role === "bank_officer";

  return (
    <header className="sticky top-0 z-50 w-full border-b border-zinc-200 bg-white/95 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/95 shadow-xs">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white font-black text-lg shadow-sm group-hover:bg-indigo-700 transition">
              R
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black tracking-wider text-base text-zinc-900 dark:text-zinc-50">
                  RIPPLE
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 font-semibold border border-zinc-200 dark:border-zinc-700">
                  Prototype
                </span>
              </div>
              <p className="text-[10px] text-zinc-500 dark:text-zinc-400 leading-tight">
                Explainable SME Credit Risk
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
            {isBank ? (
              <>
                <Link
                  href="/bank"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                    pathname === "/bank"
                      ? "bg-zinc-100 text-indigo-700 dark:bg-zinc-800 dark:text-indigo-400 font-semibold"
                      : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
                  }`}
                >
                  <Building2 className="w-4 h-4" />
                  Portfolio Dashboard
                </Link>
                <Link
                  href="/bank/assess"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                    pathname.startsWith("/bank/assess")
                      ? "bg-zinc-100 text-indigo-700 dark:bg-zinc-800 dark:text-indigo-400 font-semibold"
                      : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
                  }`}
                >
                  <Activity className="w-4 h-4" />
                  Assessment Wizard
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/sme"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                    pathname === "/sme"
                      ? "bg-zinc-100 text-indigo-700 dark:bg-zinc-800 dark:text-indigo-400 font-semibold"
                      : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
                  }`}
                >
                  <ShieldCheck className="w-4 h-4" />
                  Credit Readiness
                </Link>
                <Link
                  href="/sme/upload"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                    pathname === "/sme/upload"
                      ? "bg-zinc-100 text-indigo-700 dark:bg-zinc-800 dark:text-indigo-400 font-semibold"
                      : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
                  }`}
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  Upload Statements
                </Link>
              </>
            )}
          </nav>
        </div>

        {/* Right Controls: Health & Role Switcher */}
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
            className="hidden sm:flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900"
          >
            {systemReady === true ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="text-zinc-700 dark:text-zinc-300">Backend Ready</span>
              </>
            ) : systemReady === false ? (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                <span className="text-zinc-700 dark:text-zinc-300">Offline</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-zinc-400 animate-pulse"></span>
                <span className="text-zinc-500">Connecting</span>
              </>
            )}
          </div>

          {/* Role Switcher */}
          <div className="flex items-center bg-zinc-100 dark:bg-zinc-900 p-1 rounded-lg border border-zinc-200 dark:border-zinc-800">
            <button
              onClick={() => setRole("bank_officer")}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                isBank
                  ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-xs"
                  : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900"
              }`}
            >
              <Users className="w-3.5 h-3.5 text-indigo-600" />
              Bank Officer
            </button>
            <button
              onClick={() => setRole("sme_user")}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                !isBank
                  ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-xs"
                  : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900"
              }`}
            >
              <Building2 className="w-3.5 h-3.5 text-emerald-600" />
              SME Portal
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
