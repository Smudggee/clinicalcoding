import { MOCK_CASES, MOCK_AUDIT } from "./mockData";
import type { CaseItem, AuditEntry, AuthState, PredictedCode, SystemSettings } from "./types";

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

async function responseError(res: Response, fallback: string): Promise<Error> {
  try {
    const body = await res.json();
    return new Error(typeof body?.detail === "string" ? body.detail : fallback);
  } catch {
    return new Error(fallback);
  }
}

function isNetworkFailure(error: unknown): error is Error {
  return error instanceof Error && ["TypeError", "AbortError", "TimeoutError"].includes(error.name);
}

function canUseLocalDemoFallback(caseId: string, error: unknown): boolean {
  return isNetworkFailure(error) && casesState.find((c) => c.id === caseId)?.dataSource === "mock";
}

function actionFailure(action: string, error: unknown): Error {
  if (isNetworkFailure(error)) {
    return new Error(`${action} could not reach the backend. No changes were saved.`);
  }
  return error instanceof Error ? error : new Error(`${action} failed.`);
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
      const liveCases: CaseItem[] = (await res.json()).map((c: CaseItem) => ({ ...c, dataSource: "backend" as const }));
      casesState = liveCases;
      return liveCases;
    }
  } catch (e) {
    console.warn("[API] Failed to fetch live cases from backend, using local store:", e);
  }

  await delay(200);
  if (!_token) throw new Error("Unauthorized");
  if (status) return casesState.filter((c) => c.status === status).map((c) => ({ ...c, dataSource: "mock" as const }));
  return casesState.map((c) => ({ ...c, dataSource: "mock" as const }));
}

export async function apiGetCase(caseId: string): Promise<CaseItem> {
  try {
    const res = await fetch(`${API_BASE}/api/cases/${encodeURIComponent(caseId)}`, {
      headers: authHeaders(),
      signal: AbortSignal.timeout(2500),
    });
    if (res.ok) {
      return { ...(await res.json()), dataSource: "backend" };
    }
  } catch (e) {
    console.warn("[API] Failed to fetch live case, using local store:", e);
  }

  await delay(200);
  if (!_token) throw new Error("Unauthorized");
  const c = casesState.find((x) => x.id === caseId);
  if (!c) throw new Error("Case not found");
  return { ...c, dataSource: "mock" };
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
      const newCase: CaseItem = { ...(await res.json()), dataSource: "backend" };
      casesState.unshift(newCase);
      return newCase;
    }
    throw await responseError(res, `Analysis failed (${res.status}).`);
  } catch (e) {
    if (e instanceof Error && e.message.startsWith("Clinical note analysis failed:")) throw e;
    if (e instanceof Error && e.name !== "TypeError" && e.name !== "AbortError") throw e;
    throw new Error("Clinical note analysis is unavailable because the backend could not be reached. No predictions were generated.");
  }
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
    throw await responseError(res, `Could not confirm code (${res.status}).`);
  } catch (e) {
    if (!canUseLocalDemoFallback(caseId, e)) throw actionFailure("Confirming this code", e);
    console.warn("[API] Backend unavailable; confirming code in local demo state:", e);
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

export async function apiRejectCode(
  caseId: string,
  codeId: string,
  reason: string,
  coderName: string
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/cases/${encodeURIComponent(caseId)}/codes/${encodeURIComponent(codeId)}/reject`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ reason, coderName }),
      signal: AbortSignal.timeout(2500),
    });
    if (res.ok) return;
    throw await responseError(res, `Could not reject code (${res.status}).`);
  } catch (e) {
    if (!canUseLocalDemoFallback(caseId, e)) throw actionFailure("Rejecting this code", e);
    console.warn("[API] Backend rejection unavailable; recording the action in local demo state:", e);
  }

  await delay(200);
  const c = casesState.find((x) => x.id === caseId);
  if (!c) throw new Error("Case not found");
  const code = c.predictedCodes.find((p) => p.id === codeId);
  if (!code) throw new Error("Code not found");
  code.userAction = "rejected";
  code.userReason = reason;
  auditState.unshift({
    id: `AUD-${Date.now()}`,
    timestamp: new Date().toISOString(),
    coderName,
    caseId,
    action: "Rejected",
    codeAffected: code.code,
    oldValue: "Pending review",
    newValue: reason,
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
    throw await responseError(res, `Could not override code (${res.status}).`);
  } catch (e) {
    if (!canUseLocalDemoFallback(caseId, e)) throw actionFailure("Overriding this code", e);
    console.warn("[API] Backend unavailable; overriding code in local demo state:", e);
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
    throw await responseError(res, `Could not submit case (${res.status}).`);
  } catch (e) {
    if (!canUseLocalDemoFallback(caseId, e)) throw actionFailure("Submitting this case", e);
    console.warn("[API] Backend unavailable; submitting case in local demo state:", e);
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
      return data.map((entry) => ({ ...entry, dataSource: "backend" }));
    }
  } catch (e) {
    console.warn("[API] Live audit log unavailable, using local store:", e);
  }

  await delay(200);
  let results = auditState;
  if (params?.caseId) results = results.filter((a) => a.caseId === params.caseId);
  if (params?.from) results = results.filter((a) => a.timestamp >= params.from!);
  if (params?.to) results = results.filter((a) => a.timestamp <= params.to! + "T23:59:59Z");
  return results.map((entry) => ({ ...entry, dataSource: "mock" }));
}

// --- Admin Settings ---
export async function apiGetSettings(): Promise<SystemSettings> {
  const res = await fetch(`${API_BASE}/api/admin/settings`, {
    headers: authHeaders(),
    signal: AbortSignal.timeout(2500),
  });
  if (!res.ok) throw await responseError(res, `Could not load settings (${res.status}).`);
  return await res.json();
}

export async function apiUpdateSettings(settings: SystemSettings): Promise<SystemSettings> {
  const res = await fetch(`${API_BASE}/api/admin/settings`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(settings),
    signal: AbortSignal.timeout(2500),
  });
  if (!res.ok) throw await responseError(res, `Could not save settings (${res.status}).`);
  return await res.json();
}
