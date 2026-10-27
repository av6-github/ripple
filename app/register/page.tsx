"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { AppRole } from "@/lib/types";
import {
  Lock,
  Mail,
  Building2,
  ShieldCheck,
  User,
  Building,
  ArrowRight,
  AlertCircle,
  Loader2,
  FileText,
} from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [role, setRole] = useState<AppRole>("sme_user");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [organization, setOrganization] = useState("");
  const [taxId, setTaxId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setIsLoading(true);

    try {
      const res = await register({
        email,
        password,
        role,
        first_name: firstName,
        last_name: lastName,
        organization: organization || (role === "bank_officer" ? "Commercial Bank" : "Polish SME Enterprise"),
        tax_id: role === "sme_user" ? (taxId || `PL-${Math.floor(1000000000 + Math.random() * 9000000000)}`) : undefined,
      });

      if (res.user.role === "bank_officer") {
        router.push("/bank");
      } else {
        router.push("/sme");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setIsLoading(false);
    }
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
            Create a RIPPLE Account
          </h1>
          <p className="mt-1 text-xs text-[#2f6690]">
            Select your professional role to configure access
          </p>
        </div>

        {/* Role Selector Tabs */}
        <div className="grid grid-cols-2 gap-2 p-1.5 rounded-xl border border-[#3a7ca5]/40 bg-[#d9dcd6]">
          <button
            type="button"
            onClick={() => setRole("sme_user")}
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-bold transition cursor-pointer ${
              role === "sme_user"
                ? "bg-[#2f6690] text-[#d9dcd6] shadow-xs"
                : "text-[#2f6690] hover:text-[#16425b] hover:bg-[#3a7ca5]/10"
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>SME Borrower</span>
          </button>
          <button
            type="button"
            onClick={() => setRole("bank_officer")}
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-bold transition cursor-pointer ${
              role === "bank_officer"
                ? "bg-[#16425b] text-[#81c3d7] shadow-xs"
                : "text-[#2f6690] hover:text-[#16425b] hover:bg-[#3a7ca5]/10"
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>Bank Officer</span>
          </button>
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
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#16425b] mb-1.5">
                First Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-[#3a7ca5] absolute left-3 top-3 pointer-events-none" />
                <input
                  type="text"
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Jan"
                  className="w-full pl-9 pr-3 py-2 text-sm bg-[#d9dcd6] text-[#16425b] placeholder-[#2f6690]/60 border border-[#3a7ca5]/50 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-[#2f6690] focus:border-transparent transition"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#16425b] mb-1.5">
                Last Name
              </label>
              <input
                type="text"
                required
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Kowalski"
                className="w-full px-3 py-2 text-sm bg-[#d9dcd6] text-[#16425b] placeholder-[#2f6690]/60 border border-[#3a7ca5]/50 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-[#2f6690] focus:border-transparent transition"
              />
            </div>
          </div>

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
                placeholder={role === "bank_officer" ? "analyst@bank.pl" : "owner@enterprise.pl"}
                className="w-full pl-9 pr-3 py-2 text-sm bg-[#d9dcd6] text-[#16425b] placeholder-[#2f6690]/60 border border-[#3a7ca5]/50 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-[#2f6690] focus:border-transparent transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#16425b] mb-1.5">
              Password (Min 8 Characters)
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#3a7ca5] absolute left-3 top-3 pointer-events-none" />
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 text-sm bg-[#d9dcd6] text-[#16425b] placeholder-[#2f6690]/60 border border-[#3a7ca5]/50 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-[#2f6690] focus:border-transparent transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#16425b] mb-1.5">
              {role === "bank_officer" ? "Financial Institution / Department" : "Enterprise Legal Name"}
            </label>
            <div className="relative">
              <Building className="w-4 h-4 text-[#3a7ca5] absolute left-3 top-3 pointer-events-none" />
              <input
                type="text"
                required
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                placeholder={role === "bank_officer" ? "PKO BP Credit Risk Div." : "Baltic Logistics Sp. z o.o."}
                className="w-full pl-9 pr-3 py-2 text-sm bg-[#d9dcd6] text-[#16425b] placeholder-[#2f6690]/60 border border-[#3a7ca5]/50 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-[#2f6690] focus:border-transparent transition"
              />
            </div>
          </div>

          {role === "sme_user" && (
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#16425b] mb-1.5">
                Tax ID / NIP (Optional)
              </label>
              <div className="relative">
                <FileText className="w-4 h-4 text-[#3a7ca5] absolute left-3 top-3 pointer-events-none" />
                <input
                  type="text"
                  value={taxId}
                  onChange={(e) => setTaxId(e.target.value)}
                  placeholder="PL-5219483011"
                  className="w-full pl-9 pr-3 py-2 text-sm bg-[#d9dcd6] text-[#16425b] placeholder-[#2f6690]/60 border border-[#3a7ca5]/50 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-[#2f6690] focus:border-transparent transition"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 px-4 rounded-lg bg-[#2f6690] hover:bg-[#16425b] text-[#d9dcd6] font-bold text-sm flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Creating Account...</span>
              </>
            ) : (
              <>
                <span>Complete Registration</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer Link */}
        <div className="text-center pt-2">
          <p className="text-xs text-[#2f6690]">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-bold text-[#16425b] underline decoration-[#3a7ca5] hover:text-[#2f6690]"
            >
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
