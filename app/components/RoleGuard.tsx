"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AppRole } from "@/lib/types";
import { ShieldAlert, Loader2 } from "lucide-react";

interface RoleGuardProps {
  children: React.ReactNode;
  allowedRoles: AppRole[];
  fallbackPath?: string;
}

export function RoleGuard({ children, allowedRoles, fallbackPath }: RoleGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, role, user } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      const returnUrl = encodeURIComponent(pathname);
      router.push(`/login?returnUrl=${returnUrl}`);
      return;
    }

    if (!allowedRoles.includes(role)) {
      if (fallbackPath) {
        router.push(fallbackPath);
      } else if (role === "sme_user") {
        router.push("/sme");
      } else if (role === "bank_officer") {
        router.push("/bank");
      } else {
        router.push("/");
      }
    }
  }, [isAuthenticated, isLoading, role, allowedRoles, fallbackPath, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center bg-[#d9dcd6] text-[#16425b]">
        <Loader2 className="w-8 h-8 text-[#2f6690] animate-spin mb-3" />
        <p className="text-sm font-medium text-[#2f6690]">Verifying secure session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center bg-[#d9dcd6] text-[#16425b] px-4">
        <div className="max-w-md w-full bg-[#d9dcd6] border border-[#3a7ca5]/40 rounded-xl p-6 text-center shadow-sm">
          <ShieldAlert className="w-10 h-10 text-[#2f6690] mx-auto mb-3" />
          <h2 className="text-lg font-bold text-[#16425b] mb-1">Authentication Required</h2>
          <p className="text-xs text-[#2f6690] mb-4">
            You must be signed in to view this credit assessment view.
          </p>
          <a
            href={`/login?returnUrl=${encodeURIComponent(pathname)}`}
            className="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-[#d9dcd6] bg-[#2f6690] hover:bg-[#16425b] rounded-lg transition shadow-xs"
          >
            Go to Login
          </a>
        </div>
      </div>
    );
  }

  if (!allowedRoles.includes(role)) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center bg-[#d9dcd6] text-[#16425b] px-4">
        <div className="max-w-md w-full bg-[#d9dcd6] border border-red-300 rounded-xl p-6 text-center shadow-sm">
          <ShieldAlert className="w-10 h-10 text-red-600 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-[#16425b] mb-1">Access Denied (Rule 4.8)</h2>
          <p className="text-xs text-[#2f6690] mb-4">
            Your current account role (<span className="font-mono font-bold text-[#16425b]">{role}</span>) is not permitted to view this module.
          </p>
          <button
            onClick={() => router.push(role === "sme_user" ? "/sme" : "/bank")}
            className="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-[#d9dcd6] bg-[#2f6690] hover:bg-[#16425b] rounded-lg transition shadow-xs"
          >
            Return to Authorized Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
