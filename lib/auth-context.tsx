"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { AppRole, AuthResponse, AuthUser, LoginRequest, RegisterRequest } from "./types";
import { api } from "./api";

interface AuthContextType {
  user: AuthUser | null;
  role: AppRole;
  userEmail: string;
  smeId: string | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<AuthResponse>;
  register: (payload: RegisterRequest) => Promise<AuthResponse>;
  logout: () => void;
  setRole: (role: AppRole, customSmeId?: string) => void;
  setSmeId: (smeId: string) => void;
}

const STORAGE_KEY_TOKEN = "ripple_auth_token";
const STORAGE_KEY_USER = "ripple_auth_user";

const DEFAULT_BANK_TOKEN =
  process.env.NEXT_PUBLIC_DEMO_BANK_TOKEN ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJlbWFpbCI6Im9mZmljZXJAYmFuay5wbCIsInJvbGUiOiJiYW5rX29mZmljZXIiLCJzbWVfaWQiOm51bGwsImlhdCI6MTc5MDAyMTkxOSwiZXhwIjoxODIxNTU3OTE5fQ.xfsnOoKnjDF9mgxVU9o4-J9gdAD-w2-tQ4wIbgOyYpA";

const DEFAULT_BANK_USER: AuthUser = {
  id: "00000000-0000-0000-0000-000000000001",
  email: "officer@bank.pl",
  role: "bank_officer",
  first_name: "Wojciech",
  last_name: "Kowalski",
  organization: "PKO Commercial Credit Risk",
  sme_id: null,
};

const DEFAULT_SME_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDIiLCJlbWFpbCI6Im93bmVyQHBvbHRlY2gucGwiLCJyb2xlIjoic21lX3VzZXIiLCJzbWVfaWQiOiIzOTg4YWFhNC03MmIyLTRlZDYtOTFkYS1hZjY5NTdjMWM3NTAiLCJpYXQiOjE3OTAwMjIzNzYsImV4cCI6MTgyMTU1ODM3Nn0.ZT6nGSs83ArCMh9sk7Rq7HheJg4vnmEF2HXdTXg-N0U";

const DEFAULT_SME_USER: AuthUser = {
  id: "00000000-0000-0000-0000-000000000002",
  email: "owner@poltech.pl",
  role: "sme_user",
  first_name: "Stanisław",
  last_name: "Nowak",
  organization: "PolTech Solutions Sp. z o.o.",
  sme_id: "3988aaa4-72b2-4ed6-91da-af6957c1c750",
};

const AuthContext = createContext<AuthContextType>({
  user: DEFAULT_BANK_USER,
  role: "bank_officer",
  userEmail: "officer@bank.pl",
  smeId: null,
  token: DEFAULT_BANK_TOKEN,
  isAuthenticated: true,
  isLoading: false,
  login: async () => {
    throw new Error("AuthProvider not initialized");
  },
  register: async () => {
    throw new Error("AuthProvider not initialized");
  },
  logout: () => {},
  setRole: () => {},
  setSmeId: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(DEFAULT_BANK_USER);
  const [token, setToken] = useState<string | null>(DEFAULT_BANK_TOKEN);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Restore session from localStorage on initial mount
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem(STORAGE_KEY_TOKEN);
      const storedUser = localStorage.getItem(STORAGE_KEY_USER);

      if (storedToken && storedUser) {
        const parsedUser = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(parsedUser);
        api.setToken(storedToken);
      } else {
        // Prototype academic default: start authenticated as Bank Officer
        setToken(DEFAULT_BANK_TOKEN);
        setUser(DEFAULT_BANK_USER);
        api.setToken(DEFAULT_BANK_TOKEN);
        localStorage.setItem(STORAGE_KEY_TOKEN, DEFAULT_BANK_TOKEN);
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(DEFAULT_BANK_USER));
      }
    } catch {
      setToken(DEFAULT_BANK_TOKEN);
      setUser(DEFAULT_BANK_USER);
      api.setToken(DEFAULT_BANK_TOKEN);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (credentials: LoginRequest): Promise<AuthResponse> => {
    setIsLoading(true);
    try {
      const res = await api.login(credentials);
      setToken(res.access_token);
      setUser(res.user);
      api.setToken(res.access_token);

      localStorage.setItem(STORAGE_KEY_TOKEN, res.access_token);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(res.user));
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterRequest): Promise<AuthResponse> => {
    setIsLoading(true);
    try {
      const res = await api.register(payload);
      setToken(res.access_token);
      setUser(res.user);
      api.setToken(res.access_token);

      localStorage.setItem(STORAGE_KEY_TOKEN, res.access_token);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(res.user));
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    // Reset to demo default instead of bricking the prototype session
    setUser(DEFAULT_BANK_USER);
    setToken(DEFAULT_BANK_TOKEN);
    api.setToken(DEFAULT_BANK_TOKEN);
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
  };

  const setRole = (newRole: AppRole, customSmeId?: string) => {
    if (newRole === "sme_user") {
      const targetSmeId = customSmeId || DEFAULT_SME_USER.sme_id;
      const smeUser: AuthUser = {
        ...DEFAULT_SME_USER,
        sme_id: targetSmeId,
      };
      setUser(smeUser);
      setToken(DEFAULT_SME_TOKEN);
      api.setToken(DEFAULT_SME_TOKEN);
      localStorage.setItem(STORAGE_KEY_TOKEN, DEFAULT_SME_TOKEN);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(smeUser));
    } else {
      setUser(DEFAULT_BANK_USER);
      setToken(DEFAULT_BANK_TOKEN);
      api.setToken(DEFAULT_BANK_TOKEN);
      localStorage.setItem(STORAGE_KEY_TOKEN, DEFAULT_BANK_TOKEN);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(DEFAULT_BANK_USER));
    }
  };

  const setSmeId = (newSmeId: string) => {
    if (user) {
      const updatedUser: AuthUser = { ...user, sme_id: newSmeId };
      setUser(updatedUser);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(updatedUser));
    }
  };

  const role: AppRole = user?.role || "bank_officer";
  const userEmail = user?.email || "";
  const smeId = user?.sme_id || null;
  const isAuthenticated = true;

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        userEmail,
        smeId,
        token,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        setRole,
        setSmeId,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
