"use client";

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  Lock,
  Mail,
  Building2,
  ShieldCheck,
  ArrowRight,
  AlertCircle,
  Loader2,
  KeyRound,
  CheckCircle2,
} from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrl = searchParams.get("returnUrl");
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const res = await login({ email, password });
      if (returnUrl) {
        router.push(decodeURIComponent(returnUrl));
      } else if (res.user.role === "bank_officer") {
        router.push("/bank");
      } else {
        router.push("/sme");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid email or password.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (presetEmail: string, presetPass: string) => {
    setEmail(presetEmail);
    setPassword(presetPass);
    setError(null);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12 bg-[#d9dcd6]">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[#16425b] text-[#81c3d7] font-black text-2xl shadow-sm mb-3">
            R
          </div>
          <h1 className="text-2xl font-black tracking-tight text-[#16425b]">
            Sign in to RIPPLE
          </h1>
          <p className="mt-1 text-xs text-[#2f6690]">
            Explainable SME Credit Risk Decision Support Platform
          </p>
        </div>

        {/* 1-Click Demo Profiles Card */}
        <div className="bg-[#d9dcd6] border-2 border-[#3a7ca5]/40 rounded-xl p-4 shadow-xs">
          <div className="flex items-center gap-2 mb-2.5">
            <KeyRound className="w-4 h-4 text-[#2f6690]" />
            <span className="text-xs font-bold uppercase tracking-wider text-[#16425b]">
              Demo Quick-Fill Profiles
            </span>
          </div>
          <p className="text-[11px] text-[#2f6690] mb-3 leading-relaxed">
            Click below to instantly populate credentials for either role:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickFill("officer@bank.pl", "RippleBank2026!")}
              className="flex items-start gap-2.5 p-2.5 rounded-lg border border-[#3a7ca5]/30 bg-[#d9dcd6] hover:bg-[#3a7ca5]/15 text-left transition group cursor-pointer"
            >
              <div className="p-1 rounded bg-[#16425b] text-[#81c3d7] mt-0.5">
                <Building2 className="w-3.5 h-3.5" />
              </div>
              <div>
                <p className="text-xs font-bold text-[#16425b] group-hover:text-[#2f6690]">
                  Bank Officer
                </p>
                <p className="text-[10px] text-[#2f6690] font-mono">officer@bank.pl</p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickFill("owner@sme.pl", "RippleSme2026!")}
              className="flex items-start gap-2.5 p-2.5 rounded-lg border border-[#3a7ca5]/30 bg-[#d9dcd6] hover:bg-[#3a7ca5]/15 text-left transition group cursor-pointer"
            >
              <div className="p-1 rounded bg-[#2f6690] text-[#d9dcd6] mt-0.5">
                <ShieldCheck className="w-3.5 h-3.5" />
              </div>
              <div>
                <p className="text-xs font-bold text-[#16425b] group-hover:text-[#2f6690]">
                  SME Owner
                </p>
                <p className="text-[10px] text-[#2f6690] font-mono">owner@sme.pl</p>
              </div>
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 rounded-lg border border-red-300 bg-red-50/50 flex items-start gap-2 text-red-700 text-xs shadow-xs">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#16425b] mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-[#3a7ca5] absolute left-3 top-3 pointer-events-none" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@bank.pl"
                className="w-full pl-9 pr-3 py-2 text-sm bg-[#d9dcd6] text-[#16425b] placeholder-[#2f6690]/60 border border-[#3a7ca5]/50 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-[#2f6690] focus:border-transparent transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#16425b] mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#3a7ca5] absolute left-3 top-3 pointer-events-none" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 text-sm bg-[#d9dcd6] text-[#16425b] placeholder-[#2f6690]/60 border border-[#3a7ca5]/50 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-[#2f6690] focus:border-transparent transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 px-4 rounded-lg bg-[#2f6690] hover:bg-[#16425b] text-[#d9dcd6] font-bold text-sm flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer Link */}
        <div className="text-center pt-2">
          <p className="text-xs text-[#2f6690]">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="font-bold text-[#16425b] underline decoration-[#3a7ca5] hover:text-[#2f6690]"
            >
              Create Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[85vh] flex items-center justify-center bg-[#d9dcd6]">
          <Loader2 className="w-8 h-8 text-[#2f6690] animate-spin" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
