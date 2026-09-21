"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { AppRole } from "./types";
import { api } from "./api";

interface AuthContextType {
  role: AppRole;
  userEmail: string;
  smeId: string | null;
  token: string | null;
  setRole: (role: AppRole, customSmeId?: string) => void;
  setSmeId: (smeId: string) => void;
}

// Valid JWT tokens signed with backend default JWT_SECRET
const DEMO_BANK_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJlbWFpbCI6Im9mZmljZXJAYmFuay5wbCIsInJvbGUiOiJiYW5rX29mZmljZXIiLCJzbWVfaWQiOm51bGwsImlhdCI6MTc5MDAyMTkxOSwiZXhwIjoxODIxNTU3OTE5fQ.xfsnOoKnjDF9mgxVU9o4-J9gdAD-w2-tQ4wIbgOyYpA";

const DEMO_SME_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDIiLCJlbWFpbCI6Im93bmVyQHBvbHRlY2gucGwiLCJyb2xlIjoic21lX3VzZXIiLCJzbWVfaWQiOiIzOTg4YWFhNC03MmIyLTRlZDYtOTFkYS1hZjY5NTdjMWM3NTAiLCJpYXQiOjE3OTAwMjIzNzYsImV4cCI6MTgyMTU1ODM3Nn0.ZT6nGSs83ArCMh9sk7Rq7HheJg4vnmEF2HXdTXg-N0U";

const DEFAULT_DEMO_SME_ID = "3988aaa4-72b2-4ed6-91da-af6957c1c750";

const AuthContext = createContext<AuthContextType>({
  role: "bank_officer",
  userEmail: "officer@bank.pl",
  smeId: null,
  token: DEMO_BANK_TOKEN,
  setRole: () => {},
  setSmeId: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<AppRole>("bank_officer");
  const [smeId, setSmeIdState] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string>("officer@bank.pl");
  const [token, setToken] = useState<string | null>(DEMO_BANK_TOKEN);
  const [syncedBankToken, setSyncedBankToken] = useState<string>(DEMO_BANK_TOKEN);
  const [syncedSmeToken, setSyncedSmeToken] = useState<string>(DEMO_SME_TOKEN);
  const [syncedSmeId, setSyncedSmeId] = useState<string>(DEFAULT_DEMO_SME_ID);

  // Initialize API client token immediately
  useEffect(() => {
    api.setToken(token);
  }, [token]);

  // Dynamically synchronize tokens with running backend secret key
  useEffect(() => {
    api
      .getDemoTokens()
      .then((tokens) => {
        if (tokens?.bank_officer?.token) {
          setSyncedBankToken(tokens.bank_officer.token);
          if (role === "bank_officer") {
            setToken(tokens.bank_officer.token);
            api.setToken(tokens.bank_officer.token);
          }
        }
        if (tokens?.sme_user?.token) {
          setSyncedSmeToken(tokens.sme_user.token);
          const resolvedSme = (tokens.sme_user as { sme_id?: string })?.sme_id || DEFAULT_DEMO_SME_ID;
          setSyncedSmeId(resolvedSme);
          if (role === "sme_user") {
            setToken(tokens.sme_user.token);
            api.setToken(tokens.sme_user.token);
            setSmeIdState(resolvedSme);
          }
        }
      })
      .catch(() => {
        // Fallback to static prototype tokens
      });
  }, [role]);

  const setRole = (newRole: AppRole, customSmeId?: string) => {
    setRoleState(newRole);
    if (newRole === "bank_officer") {
      setUserEmail("credit_officer@bank.pl");
      setSmeIdState(null);
      setToken(syncedBankToken);
      api.setToken(syncedBankToken);
    } else {
      const targetSmeId = customSmeId || smeId || syncedSmeId || DEFAULT_DEMO_SME_ID;
      setUserEmail("director@poltech.pl");
      setSmeIdState(targetSmeId);
      setToken(syncedSmeToken);
      api.setToken(syncedSmeToken);
    }
  };

  const setSmeId = (newSmeId: string) => {
    setSmeIdState(newSmeId);
  };

  return (
    <AuthContext.Provider
      value={{
        role,
        userEmail,
        smeId,
        token,
        setRole,
        setSmeId,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
