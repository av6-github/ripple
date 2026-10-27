import {
  AssessmentResponse,
  AssessmentSnapshotRecord,
  AuthResponse,
  AuthUser,
  IngestionJobResult,
  LoginRequest,
  OfficerDecisionRecord,
  QuantAnalyticsReport,
  RegisterRequest,
  ScenarioResult,
  SmeProfile,
  SmeReadinessResponse,
  StatementPeriod,
  LoanApplicationRecord,
  CreateLoanApplicationRequest,
} from "./types";

const getApiBase = () => {
  if (typeof window !== "undefined") {
    // In browser environment, use same-origin relative URLs ("") which are transparently
    // proxied to FastAPI backend via Next.js rewrites, guaranteeing zero cross-origin/CORS
    // blocks and avoiding IPv6/IPv4 address resolution mismatches on Linux/Firefox.
    return "";
  }
  return (
    process.env.BACKEND_INTERNAL_URL ||
    process.env.NEXT_PUBLIC_API_BASE ||
    "http://127.0.0.1:8000"
  );
};

const DEFAULT_BANK_TOKEN =
  process.env.NEXT_PUBLIC_DEMO_BANK_TOKEN ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJlbWFpbCI6Im9mZmljZXJAYmFuay5wbCIsInJvbGUiOiJiYW5rX29mZmljZXIiLCJzbWVfaWQiOm51bGwsImlhdCI6MTc5MDAyMTkxOSwiZXhwIjoxODIxNTU3OTE5fQ.xfsnOoKnjDF9mgxVU9o4-J9gdAD-w2-tQ4wIbgOyYpA";

class ApiClient {
  private token: string | null = DEFAULT_BANK_TOKEN;

  setToken(token: string | null) {
    this.token = token;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    const activeToken = this.token || DEFAULT_BANK_TOKEN;
    if (activeToken) {
      headers["Authorization"] = `Bearer ${activeToken}`;
    }
    return headers;
  }

  private async fetchWithFallback(urlOrPath: string, init?: RequestInit): Promise<Response> {
    let finalUrl = urlOrPath;
    if (!urlOrPath.startsWith("http://") && !urlOrPath.startsWith("https://")) {
      const base = getApiBase();
      finalUrl = base ? `${base}${urlOrPath.startsWith("/") ? urlOrPath : `/${urlOrPath}`}` : urlOrPath;
    }

    try {
      return await fetch(finalUrl, init);
    } catch (err: unknown) {
      // If primary fetch failed with a NetworkError in the browser, fallback to direct loopback
      if (typeof window !== "undefined") {
        const path = finalUrl.startsWith("http")
          ? new URL(finalUrl).pathname + new URL(finalUrl).search
          : finalUrl;
        const candidates = ["http://127.0.0.1:8000", "http://localhost:8000"];
        for (const host of candidates) {
          const candidateUrl = `${host}${path.startsWith("/") ? path : `/${path}`}`;
          if (candidateUrl !== finalUrl) {
            try {
              return await fetch(candidateUrl, init);
            } catch {
              // try next candidate
            }
          }
        }
      }
      throw err;
    }
  }

  async checkHealth(): Promise<{ status: string; service: string }> {
    const res = await this.fetchWithFallback("/health");
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  }

  async checkReady(): Promise<Record<string, unknown>> {
    const res = await this.fetchWithFallback("/ready");
    if (!res.ok) throw new Error("Readiness check failed");
    return res.json();
  }

  async getDemoTokens(): Promise<Record<string, { token: string; role: string; email: string }>> {
    const res = await this.fetchWithFallback("/api/auth/demo-tokens");
    if (!res.ok) throw new Error("Failed to fetch synchronized demo tokens");
    return res.json();
  }

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const res = await this.fetchWithFallback("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(err.detail || "Authentication failed. Check credentials.");
    }
    const data: AuthResponse = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(payload: RegisterRequest): Promise<AuthResponse> {
    const res = await this.fetchWithFallback("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Registration failed" }));
      throw new Error(err.detail || "Registration failed.");
    }
    const data: AuthResponse = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  async getMe(): Promise<AuthUser> {
    const res = await this.fetchWithFallback("/api/auth/me", {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch profile");
    return res.json();
  }

  // Bank endpoints (with graceful SME user tenant isolation fallback)
  async listSmes(): Promise<SmeProfile[]> {
    let res = await this.fetchWithFallback("/api/bank/smes", {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      if (res.status === 401) {
        // Automatic retry with prototype demo token if token was invalid/stale
        this.token = DEFAULT_BANK_TOKEN;
        res = await this.fetchWithFallback("/api/bank/smes", {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${DEFAULT_BANK_TOKEN}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          const rawSmes: SmeProfile[] = Array.isArray(data) ? data : (data.smes || []);
          return this.sanitizeAndDeduplicateSmes(rawSmes);
        }
      }
      if (res.status === 403) {
        // Fallback for SME user role (Rule 4.8 SME tenant isolation: retrieve own profile)
        try {
          const profileRes = await this.fetchWithFallback("/api/sme/profile", {
            headers: this.getHeaders(),
          });
          if (profileRes.ok) {
            const profileData = await profileRes.json();
            if (profileData?.sme) {
              return [profileData.sme];
            }
          }
        } catch {
          // ignore and fallback to readiness
        }
        try {
          const readyRes = await this.fetchWithFallback("/api/sme/readiness", {
            headers: this.getHeaders(),
          });
          if (readyRes.ok) {
            const readyData = await readyRes.json();
            if (readyData?.sme_id) {
              return [
                {
                  id: readyData.sme_id,
                  legal_name: readyData.business_name || "Self-Registered SME",
                  tax_id: "PL-SME",
                  created_at: new Date().toISOString(),
                },
              ];
            }
          }
        } catch {
          // ignore
        }
        return [];
      }
      throw new Error(`Failed to list SMEs (${res.status})`);
    }
    const data = await res.json();
    const rawSmes: SmeProfile[] = Array.isArray(data) ? data : (data.smes || []);
    return this.sanitizeAndDeduplicateSmes(rawSmes);
  }

  private sanitizeAndDeduplicateSmes(smes: SmeProfile[]): SmeProfile[] {
    const cleanMap = new Map<string, SmeProfile>();
    for (const s of smes) {
      if (!s || !s.legal_name) continue;
      const rawName = s.legal_name.trim();
      if (
        rawName.startsWith("Test ") ||
        rawName.startsWith("Assessment Target ") ||
        rawName.startsWith("Zielinski") ||
        (s.tax_id && (s.tax_id.startsWith("TAX-") || s.tax_id.startsWith("BYR-") || s.tax_id.startsWith("SUP-") || s.tax_id.startsWith("PRT-")))
      ) {
        continue;
      }
      const cleanName = rawName.split("[ID:")[0].split("[")[0].trim();
      if (!cleanMap.has(cleanName)) {
        cleanMap.set(cleanName, { ...s, legal_name: cleanName });
      }
    }
    return Array.from(cleanMap.values());
  }

  async getSmeProfile(
    smeId: string
  ): Promise<{ sme: SmeProfile; assessments: AssessmentSnapshotRecord[] }> {
    const res = await this.fetchWithFallback(`/api/bank/smes/${smeId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to get SME profile (${res.status})`);
    return res.json();
  }

  async getSmeCounterparties(smeId: string): Promise<{
    sme_id: string;
    tax_id: string;
    count: number;
    counterparties: any[];
    edges: [number, number][];
  }> {
    const res = await this.fetchWithFallback(`/api/bank/smes/${smeId}/counterparties`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch counterparties (${res.status})`);
    return res.json();
  }

  async runAssessment(params: {
    sme_id: string;
    statements: StatementPeriod[];
    network_neighbors?: string[];
    network_edges?: [number, number][];
    application_id?: string;
  }): Promise<AssessmentResponse> {
    const res = await this.fetchWithFallback("/api/bank/assessments/run", {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Assessment error" }));
      throw new Error(err.detail || `Assessment failed with status ${res.status}`);
    }
    return res.json();
  }

  async getAssessment(
    assessmentId: string
  ): Promise<{
    assessment: AssessmentSnapshotRecord;
    officer_decisions: OfficerDecisionRecord[];
  }> {
    const res = await this.fetchWithFallback(`/api/bank/assessments/${assessmentId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to get assessment snapshot (${res.status})`);
    return res.json();
  }

  async recordOfficerDecision(
    assessmentId: string,
    decisionData: {
      decision: string;
      is_override: boolean;
      override_reason?: string;
      comments?: string;
    }
  ): Promise<{ status: string; decision: OfficerDecisionRecord }> {
    const res = await this.fetchWithFallback(
      `/api/bank/assessments/${assessmentId}/decision`,
      {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(decisionData),
      }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Decision submission failed" }));
      throw new Error(err.detail || `Failed with status ${res.status}`);
    }
    return res.json();
  }

  async getAssessmentQuantAnalytics(assessmentId: string): Promise<QuantAnalyticsReport> {
    const res = await this.fetchWithFallback(
      `/api/bank/assessments/${assessmentId}/quant-analytics`,
      { headers: this.getHeaders() }
    );
    if (!res.ok) {
      throw new Error(`Failed to fetch quant analytics (${res.status})`);
    }
    return res.json();
  }

  async simulateScenario(
    assessmentId: string,
    params: {
      revenue_drop_pct: number;
      rate_hike_bps: number;
      dso_increase_days: number;
      cost_inflation_pct: number;
    }
  ): Promise<ScenarioResult> {
    let res = await this.fetchWithFallback(
      `/api/bank/assessments/${assessmentId}/simulate-scenario`,
      {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(params),
      }
    );
    if (!res.ok) {
      if (res.status === 401) {
        this.token = DEFAULT_BANK_TOKEN;
        res = await this.fetchWithFallback(
          `/api/bank/assessments/${assessmentId}/simulate-scenario`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${DEFAULT_BANK_TOKEN}`,
            },
            body: JSON.stringify(params),
          }
        );
      }
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Scenario simulation failed" }));
      throw new Error(err.detail || `Failed with status ${res.status}`);
    }
    return res.json();
  }

  // SME endpoints (Strict Rule 4.8 data redaction enforced on backend)
  async getSmeReadiness(smeId?: string): Promise<SmeReadinessResponse> {
    const url = smeId
      ? `/api/sme/readiness?sme_id=${smeId}`
      : `/api/sme/readiness`;
    const res = await this.fetchWithFallback(url, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch credit readiness (${res.status})`);
    return res.json();
  }

  async uploadFinancialFile(
    smeId: string,
    file: File
  ): Promise<{ status: string; job: IngestionJobResult }> {
    const formData = new FormData();
    formData.append("file", file);

    const headers: HeadersInit = {};
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await this.fetchWithFallback(`/api/sme/upload?sme_id=${smeId}`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || `Upload failed with status ${res.status}`);
    }
    return res.json();
  }

  // Loan Applications - Bank
  async listLoanApplications(status?: string): Promise<LoanApplicationRecord[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    let res = await this.fetchWithFallback(`/api/bank/applications${query}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok && res.status === 401) {
      res = await this.fetchWithFallback(`/api/bank/applications${query}`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${DEFAULT_BANK_TOKEN}`,
        },
      });
    }
    if (!res.ok) {
      return [];
    }
    const data = await res.json();
    return Array.isArray(data) ? data : data.applications || [];
  }

  async createLoanApplication(
    payload: CreateLoanApplicationRequest
  ): Promise<{ status: string; application: LoanApplicationRecord }> {
    const res = await this.fetchWithFallback("/api/bank/applications", {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Loan intake recording failed" }));
      throw new Error(err.detail || `Failed with status ${res.status}`);
    }
    return res.json();
  }

  async getLoanApplication(
    applicationId: string
  ): Promise<{ application: LoanApplicationRecord }> {
    const res = await this.fetchWithFallback(`/api/bank/applications/${applicationId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to get loan application (${res.status})`);
    return res.json();
  }

  // Loan Applications - SME
  async submitSmeLoanApplication(
    payload: CreateLoanApplicationRequest
  ): Promise<{ status: string; application: LoanApplicationRecord }> {
    const res = await this.fetchWithFallback("/api/sme/applications", {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Loan application submission failed" }));
      throw new Error(err.detail || `Failed with status ${res.status}`);
    }
    return res.json();
  }

  async listSmeLoanApplications(): Promise<LoanApplicationRecord[]> {
    const res = await this.fetchWithFallback("/api/sme/applications", {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      return [];
    }
    const data = await res.json();
    return Array.isArray(data) ? data : data.applications || [];
  }
}

export const api = new ApiClient();
