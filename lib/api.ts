import {
  AssessmentResponse,
  AssessmentSnapshotRecord,
  OfficerDecisionRecord,
  SmeProfile,
  SmeReadinessResponse,
  StatementPeriod,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

const DEFAULT_BANK_TOKEN =
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
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async checkHealth(): Promise<{ status: string; service: string }> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  }

  async checkReady(): Promise<Record<string, unknown>> {
    const res = await fetch(`${API_BASE}/ready`);
    if (!res.ok) throw new Error("Readiness check failed");
    return res.json();
  }

  async getDemoTokens(): Promise<Record<string, { token: string; role: string; email: string }>> {
    const res = await fetch(`${API_BASE}/api/auth/demo-tokens`);
    if (!res.ok) throw new Error("Failed to fetch synchronized demo tokens");
    return res.json();
  }

  // Bank endpoints
  async listSmes(): Promise<SmeProfile[]> {
    const res = await fetch(`${API_BASE}/api/bank/smes`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to list SMEs (${res.status})`);
    const data = await res.json();
    return Array.isArray(data) ? data : (data.smes || []);
  }

  async getSmeProfile(
    smeId: string
  ): Promise<{ sme: SmeProfile; assessments: AssessmentSnapshotRecord[] }> {
    const res = await fetch(`${API_BASE}/api/bank/smes/${smeId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to get SME profile (${res.status})`);
    return res.json();
  }

  async runAssessment(params: {
    sme_id: string;
    statements: StatementPeriod[];
    network_neighbors?: string[];
    network_edges?: [number, number][];
  }): Promise<AssessmentResponse> {
    const res = await fetch(`${API_BASE}/api/bank/assessments/run`, {
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
    const res = await fetch(`${API_BASE}/api/bank/assessments/${assessmentId}`, {
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
    const res = await fetch(
      `${API_BASE}/api/bank/assessments/${assessmentId}/decision`,
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

  // SME endpoints (Strict Rule 4.8 data redaction enforced on backend)
  async getSmeReadiness(smeId?: string): Promise<SmeReadinessResponse> {
    const url = smeId
      ? `${API_BASE}/api/sme/readiness?sme_id=${smeId}`
      : `${API_BASE}/api/sme/readiness`;
    const res = await fetch(url, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch credit readiness (${res.status})`);
    return res.json();
  }

  async uploadFinancialFile(smeId: string, file: File): Promise<Record<string, unknown>> {
    const formData = new FormData();
    formData.append("file", file);

    const headers: HeadersInit = {};
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}/api/sme/upload?sme_id=${smeId}`, {
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
}

export const api = new ApiClient();
