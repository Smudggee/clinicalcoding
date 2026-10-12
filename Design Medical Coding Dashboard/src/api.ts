import { MOCK_CASES, MOCK_AUDIT } from "./mockData";
import type { CaseItem, AuditEntry, AuthState, PredictedCode } from "./types";

const API_BASE = "http://localhost:8000";
let _token: string | null = null;

// In-memory fallback state
let casesState: CaseItem[] = JSON.parse(JSON.stringify(MOCK_CASES));
let auditState: AuditEntry[] = [...MOCK_AUDIT];

function delay(ms = 400) {
  return new Promise<void>((r) => setTimeout(r, ms));
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${_token}`,
  };
}

// --- Health / Backend Status ---
export async function apiCheckBackend(): Promise<{ isLive: boolean; version?: string }> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: "GET", signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      const data = await res.json();
      return { isLive: true, version: data.version };
    }
  } catch {
    // Backend offline
  }
  return { isLive: false };
}

// --- Auth ---
export async function apiLogin(
  username: string,
  password: string,
  role: string
): Promise<AuthState> {
  if (!username || !password) throw new Error("Invalid credentials");

  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, role }),
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      const data = await res.json();
      _token = data.token;
      return data;
    }
  } catch (e) {
    console.warn("[API] Backend login unreachable, falling back to local auth mode:", e);
  }

  // Fallback local auth
  await delay(200);
  const roleMap: Record<string, string> = {
    "Medical Coder": "Medical Coder",
    Administrator: "Administrator",
    Physician: "Physician",
  };
  _token = `mock-jwt-${Date.now()}`;
  return {
    token: _token,
    user: {
      id: "usr-local",
      name: username.includes("@") ? username.split("@")[0] : username,
      email: username.includes("@") ? username : `${username}@hospital.org`,
      role: (roleMap[role] as AuthState["user"]["role"]) || "Medical Coder",
      active: true,
    },
  };
}

export function setToken(token: string | null) {
  _token = token;
}

// --- Cases ---
export async function apiGetCases(status?: string): Promise<CaseItem[]> {
  try {
    const url = status ? `${API_BASE}/api/cases?status=${encodeURIComponent(status)}` : `${API_BASE}/api/cases`;
    const res = await fetch(url, { headers: authHeaders(), signal: AbortSignal.timeout(2500) });
    if (res.ok) {
      const liveCases: CaseItem[] = await res.json();
      casesState = liveCases;
      return liveCases;
    }
  } catch (e) {
    console.warn("[API] Failed to fetch live cases from backend, using local store:", e);
  }

  await delay(200);
  if (!_token) throw new Error("Unauthorized");
  if (status) return casesState.filter((c) => c.status === status);
  return casesState;
}

export async function apiGetCase(caseId: string): Promise<CaseItem> {
  try {
    const res = await fetch(`${API_BASE}/api/cases/${encodeURIComponent(caseId)}`, {
      headers: authHeaders(),
      signal: AbortSignal.timeout(2500),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("[API] Failed to fetch live case, using local store:", e);
  }

  await delay(200);
  if (!_token) throw new Error("Unauthorized");
  const c = casesState.find((x) => x.id === caseId);
  if (!c) throw new Error("Case not found");
  return c;
}

export async function apiAnalyzeNote(text: string, patientId?: string, documentId?: string): Promise<CaseItem> {
  try {
    const res = await fetch(`${API_BASE}/api/cases/analyze`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ text, patient_id: patientId, document_id: documentId }),
      signal: AbortSignal.timeout(10000),
    });
    if (res.ok) {
      const newCase: CaseItem = await res.json();
      casesState.unshift(newCase);
      return newCase;
    }
  } catch (e) {
    console.warn("[API] Live pipeline analysis unavailable, creating local demo case:", e);
  }

  // Fallback demo analysis
  await delay(600);
  const words = text.split(/(\s+)/).filter((t) => t.trim().length > 0);
  const docId = documentId || `CASE-${Date.now().toString().slice(-6)}`;
  const mockNewCase: CaseItem = {
    id: docId,
    patientId: patientId || `P-${Math.floor(1000 + Math.random() * 9000)}`,
    submittedAt: new Date().toISOString(),
    status: "Pending Review",
    averageConfidence: 89,
    dischargeText: text,
    words,
    predictedCodes: [
      {
        id: `c-${docId}-1`,
        code: "A41.9",
        description: "Sepsis, unspecified organism",
        confidence: 94,
        verificationStatus: "VERIFIED",
        supportingEvidence: text.slice(0, 80),
        attentionSpans: [{ startIdx: 0, endIdx: Math.min(words.length, 5), weight: 0.9 }],
      },
    ],
  };
  casesState.unshift(mockNewCase);
  return mockNewCase;
}

export async function apiConfirmCode(
  caseId: string,
  codeId: string,
  coderName: string
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/cases/${encodeURIComponent(caseId)}/codes/${encodeURIComponent(codeId)}/confirm`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ coderName }),
      signal: AbortSignal.timeout(2500),
    });
    if (res.ok) return;
  } catch (e) {
    console.warn("[API] Live confirm failed, updating local state:", e);
  }

  await delay(200);
  const c = casesState.find((x) => x.id === caseId);
  if (!c) throw new Error("Case not found");
  const code = c.predictedCodes.find((p) => p.id === codeId);
  if (!code) throw new Error("Code not found");
  code.userAction = "confirmed";
  auditState.unshift({
    id: `AUD-${Date.now()}`,
    timestamp: new Date().toISOString(),
    coderName,
    caseId,
    action: "Confirmed",
    codeAffected: code.code,
    oldValue: "—",
    newValue: "Confirmed",
  });
}

export async function apiOverrideCode(
  caseId: string,
  codeId: string,
  newCode: string,
  reason: string,
  coderName: string
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/cases/${encodeURIComponent(caseId)}/codes/${encodeURIComponent(codeId)}/override`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ newCode, reason, coderName }),
      signal: AbortSignal.timeout(2500),
    });
    if (res.ok) return;
  } catch (e) {
    console.warn("[API] Live override failed, updating local state:", e);
  }

  await delay(200);
  const c = casesState.find((x) => x.id === caseId);
  if (!c) throw new Error("Case not found");
  const code = c.predictedCodes.find((p) => p.id === codeId);
  if (!code) throw new Error("Code not found");
  const oldCode = code.code;
  code.userAction = "overridden";
  code.overrideCode = newCode;
  code.overrideReason = reason;
  auditState.unshift({
    id: `AUD-${Date.now()}`,
    timestamp: new Date().toISOString(),
    coderName,
    caseId,
    action: "Overridden",
    codeAffected: oldCode,
    oldValue: oldCode,
    newValue: newCode,
  });
}

export async function apiSubmitCase(caseId: string, coderName: string): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/cases/${encodeURIComponent(caseId)}/submit`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ coderName }),
      signal: AbortSignal.timeout(2500),
    });
    if (res.ok) return;
  } catch (e) {
    console.warn("[API] Live submit failed, updating local state:", e);
  }

  await delay(300);
  const c = casesState.find((x) => x.id === caseId);
  if (!c) throw new Error("Case not found");
  c.status = "Completed";
  c.submittedToBilling = true;
  auditState.unshift({
    id: `AUD-${Date.now()}`,
    timestamp: new Date().toISOString(),
    coderName,
    caseId,
    action: "Submitted",
    codeAffected: "ALL",
    oldValue: "—",
    newValue: "Submitted to billing",
  });
}

// --- Audit ---
export async function apiGetAudit(params?: {
  caseId?: string;
  from?: string;
  to?: string;
}): Promise<AuditEntry[]> {
  try {
    const query = new URLSearchParams();
    if (params?.caseId) query.set("caseId", params.caseId);
    if (params?.from) query.set("from", params.from);
    if (params?.to) query.set("to", params.to);

    const res = await fetch(`${API_BASE}/api/audit?${query.toString()}`, {
      headers: authHeaders(),
      signal: AbortSignal.timeout(2500),
    });
    if (res.ok) {
      const data: AuditEntry[] = await res.json();
      auditState = data;
      return data;
    }
  } catch (e) {
    console.warn("[API] Live audit log unavailable, using local store:", e);
  }

  await delay(200);
  let results = auditState;
  if (params?.caseId) results = results.filter((a) => a.caseId === params.caseId);
  if (params?.from) results = results.filter((a) => a.timestamp >= params.from!);
  if (params?.to) results = results.filter((a) => a.timestamp <= params.to! + "T23:59:59Z");
  return results;
}

// --- Admin Settings ---
export async function apiGetSettings(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/admin/settings`, { headers: authHeaders() });
    if (res.ok) return await res.json();
  } catch {
    // fallback
  }
  return {
    auto_accept_threshold: 0.85,
    review_threshold: 0.50,
    model_name: "emilyalsentzer/Bio_ClinicalBERT",
    ontology_version: "ICD-10-CM 2026",
    sliding_window_size: 512,
    sliding_stride: 256,
  };
}

export async function apiUpdateSettings(settings: any): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/admin/settings`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(settings),
    });
  } catch {
    // fallback
  }
}
