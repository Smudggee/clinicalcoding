import { useState, useEffect, useCallback } from "react";
import type { AuthState, CaseItem, PredictedCode } from "../types";
import { apiGetCase, apiConfirmCode, apiOverrideCode, apiSubmitCase } from "../api";
import { VerificationBadge } from "../components/StatusBadge";
import ConfidenceBar from "../components/ConfidenceBar";
import { CardSkeleton } from "../components/Skeleton";
import Modal from "../components/Modal";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import type { Page, Toast } from "../types";

interface Props {
  auth: AuthState;
  caseId: string;
  onSignOut: () => void;
  onNavigate: (page: Page, caseId?: string) => void;
  addToast: (type: Toast["type"], message: string) => void;
}

const OVERRIDE_REASONS = [
  "Clinical judgment",
  "Documentation error",
  "Code specificity",
  "Additional diagnosis found",
  "Duplicate code",
  "Other",
];

export default function CaseReview({ auth, caseId, onSignOut, onNavigate, addToast }: Props) {
  const [caseData, setCaseData] = useState<CaseItem | null>(null);
  const [codes, setCodes] = useState<PredictedCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredCodeId, setHoveredCodeId] = useState<string | null>(null);
  const [overrideModal, setOverrideModal] = useState<{ code: PredictedCode } | null>(null);
  const [overrideNewCode, setOverrideNewCode] = useState("");
  const [overrideReason, setOverrideReason] = useState(OVERRIDE_REASONS[0]);
  const [overrideLoading, setOverrideLoading] = useState(false);
  const [confirmSubmitOpen, setConfirmSubmitOpen] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [expandedEvidence, setExpandedEvidence] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const c = await apiGetCase(caseId);
      setCaseData(c);
      setCodes(c.predictedCodes.map((p) => ({ ...p })));
    } catch {
      addToast("error", "Failed to load case. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [caseId, addToast]);

  useEffect(() => { load(); }, [load]);

  // Compute per-word attention weights for hovered code
  const wordWeights = useCallback((): number[] => {
    if (!caseData || !hoveredCodeId) return [];
    const code = codes.find((c) => c.id === hoveredCodeId);
    if (!code) return [];
    const weights = new Array(caseData.words.length).fill(0);
    code.attentionSpans.forEach(({ startIdx, endIdx, weight }) => {
      for (let i = startIdx; i < Math.min(endIdx, weights.length); i++) {
        weights[i] = Math.max(weights[i], weight);
      }
    });
    return weights;
  }, [caseData, codes, hoveredCodeId]);

  async function handleConfirm(code: PredictedCode) {
    try {
      await apiConfirmCode(caseId, code.id, auth.user.name);
      setCodes((prev) => prev.map((c) => c.id === code.id ? { ...c, userAction: "confirmed" } : c));
      addToast("success", `Code ${code.code} confirmed.`);
    } catch {
      addToast("error", "Failed to confirm code. Please try again.");
    }
  }

  async function handleOverrideSubmit() {
    if (!overrideModal) return;
    if (!overrideNewCode.trim()) {
      addToast("warning", "Please enter a replacement ICD-10-CM code.");
      return;
    }
    setOverrideLoading(true);
    try {
      await apiOverrideCode(caseId, overrideModal.code.id, overrideNewCode.trim().toUpperCase(), overrideReason, auth.user.name);
      setCodes((prev) =>
        prev.map((c) =>
          c.id === overrideModal.code.id
            ? { ...c, userAction: "overridden", overrideCode: overrideNewCode.trim().toUpperCase(), overrideReason }
            : c
        )
      );
      addToast("success", `Code ${overrideModal.code.code} overridden with ${overrideNewCode.trim().toUpperCase()}.`);
      setOverrideModal(null);
      setOverrideNewCode("");
      setOverrideReason(OVERRIDE_REASONS[0]);
    } catch {
      addToast("error", "Override failed. Please try again.");
    } finally {
      setOverrideLoading(false);
    }
  }

  async function handleSubmitToBilling() {
    setSubmitLoading(true);
    try {
      await apiSubmitCase(caseId, auth.user.name);
      setCaseData((prev) => prev ? { ...prev, status: "Completed", submittedToBilling: true } : prev);
      addToast("success", `Case ${caseId} successfully submitted to billing.`);
      setConfirmSubmitOpen(false);
      setTimeout(() => onNavigate("dashboard"), 1500);
    } catch {
      addToast("error", "Submission failed. Please try again.");
    } finally {
      setSubmitLoading(false);
    }
  }

  const allActioned = codes.every((c) => c.userAction);
  const confirmedCount = codes.filter((c) => c.userAction === "confirmed").length;
  const overriddenCount = codes.filter((c) => c.userAction === "overridden").length;
  const pendingCount = codes.filter((c) => !c.userAction).length;
  const weights = wordWeights();

  function toggleEvidence(id: string) {
    setExpandedEvidence((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  return (
    <div className="flex min-h-screen" style={{ background: "#f8fafc" }}>
      <Sidebar currentPage="case-review" onNavigate={onNavigate} />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          auth={auth}
          title={`Case Review — ${caseId}`}
          subtitle={caseData ? `Patient ${caseData.patientId} · ${caseData.predictedCodes.length} predicted codes` : "Loading…"}
          onSignOut={onSignOut}
        />

        {/* Back nav */}
        <div className="px-6 py-3 border-b border-slate-200 bg-white flex items-center gap-3">
          <button
            onClick={() => onNavigate("dashboard")}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Back to Dashboard
          </button>
          {caseData && (
            <>
              <span className="text-slate-300">/</span>
              <span className="text-sm text-slate-700 font-medium">{caseId}</span>
              {caseData.submittedToBilling && (
                <span className="ml-2 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-success">
                  ✓ Submitted to Billing
                </span>
              )}
            </>
          )}
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Left: Discharge text with attention heatmap */}
          <div
            className="flex flex-col border-r border-slate-200 bg-white"
            style={{ width: "40%", minWidth: 380 }}
          >
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between flex-shrink-0">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Discharge Summary</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {hoveredCodeId
                    ? "Attention heatmap active — hover words show model focus"
                    : "Hover a code card to activate attention heatmap"}
                </p>
              </div>
              {hoveredCodeId && (
                <span className="flex items-center gap-1.5 text-xs font-medium text-primary">
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  Heatmap active
                </span>
              )}
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-5">
              {loading ? (
                <div className="space-y-2">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="skeleton h-4 rounded" style={{ width: `${70 + (i % 5) * 6}%` }} />
                  ))}
                </div>
              ) : caseData ? (
                <p className="text-sm leading-relaxed text-slate-700 select-text" style={{ fontFamily: "var(--font-sans)" }}>
                  {caseData.words.map((word, i) => {
                    const w = weights[i] ?? 0;
                    return (
                      <span
                        key={i}
                        className="attention-word"
                        style={{
                          backgroundColor:
                            w > 0.05
                              ? `rgba(37, 99, 235, ${Math.min(w * 0.45, 0.4)})`
                              : "transparent",
                          fontWeight: w > 0.7 ? 600 : 400,
                        }}
                        title={w > 0.05 ? `Attention weight: ${(w * 100).toFixed(0)}%` : undefined}
                      >
                        {word}{" "}
                      </span>
                    );
                  })}
                </p>
              ) : null}
            </div>

            {/* Heatmap legend */}
            <div className="px-5 py-3 border-t border-slate-100 flex items-center gap-3 flex-shrink-0">
              <span className="text-xs text-slate-400">Attention weight:</span>
              <div className="flex items-center gap-1.5">
                <div className="flex gap-0.5">
                  {[0.05, 0.15, 0.25, 0.35, 0.45].map((op, i) => (
                    <div
                      key={i}
                      className="w-4 h-3 rounded-sm"
                      style={{ background: `rgba(37,99,235,${op})` }}
                    />
                  ))}
                </div>
                <span className="text-xs text-slate-400">Low → High</span>
              </div>
            </div>
          </div>

          {/* Right: Code cards */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {loading ? (
                Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)
              ) : codes.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <circle cx="24" cy="24" r="22" stroke="#e2e8f0" strokeWidth="2" fill="none" />
                    <path d="M16 24h16M24 16v16" stroke="#cbd5e1" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                  <p className="text-sm font-medium mt-3 text-slate-500">No codes predicted</p>
                </div>
              ) : (
                codes.map((code) => {
                  const isHovered = hoveredCodeId === code.id;
                  const evidenceOpen = expandedEvidence.has(code.id);
                  const actionColor =
                    code.userAction === "confirmed"
                      ? "#16A34A"
                      : code.userAction === "overridden"
                      ? "#EA580C"
                      : undefined;

                  return (
                    <div
                      key={code.id}
                      className="bg-white rounded-xl border transition-all"
                      style={{
                        borderColor: isHovered ? "#2563EB" : code.userAction === "confirmed" ? "#bbf7d0" : code.userAction === "overridden" ? "#fed7aa" : "#e2e8f0",
                        boxShadow: isHovered ? "0 0 0 3px rgba(37,99,235,0.1)" : "none",
                      }}
                      onMouseEnter={() => setHoveredCodeId(code.id)}
                      onMouseLeave={() => setHoveredCodeId(null)}
                    >
                      <div className="p-4">
                        <div className="flex items-start justify-between gap-3 mb-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-1">
                              <span
                                className="font-bold text-xl tracking-tight"
                                style={{ fontFamily: "var(--font-mono)", color: actionColor ?? "#0B132B" }}
                              >
                                {code.userAction === "overridden" && code.overrideCode
                                  ? code.overrideCode
                                  : code.code}
                              </span>
                              {code.userAction === "overridden" && code.overrideCode && (
                                <span className="text-xs text-slate-400 line-through font-mono">{code.code}</span>
                              )}
                              <VerificationBadge status={code.verificationStatus} />
                            </div>
                            <p className="text-sm text-slate-600 leading-snug">{code.description}</p>
                          </div>

                          {code.userAction && (
                            <div
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold flex-shrink-0"
                              style={{
                                background: code.userAction === "confirmed" ? "#dcfce7" : "#ffedd5",
                                color: code.userAction === "confirmed" ? "#16A34A" : "#EA580C",
                              }}
                            >
                              {code.userAction === "confirmed" ? (
                                <>
                                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                  </svg>
                                  Confirmed
                                </>
                              ) : (
                                <>
                                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                                    <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                  </svg>
                                  Overridden
                                </>
                              )}
                            </div>
                          )}
                        </div>

                        <div className="mb-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-slate-500 font-medium">Confidence</span>
                          </div>
                          <ConfidenceBar value={code.confidence} />
                        </div>

                        {/* Evidence toggle */}
                        <button
                          onClick={() => toggleEvidence(code.id)}
                          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-primary transition-colors mb-3"
                          aria-expanded={evidenceOpen}
                        >
                          <svg
                            width="12" height="12" viewBox="0 0 12 12" fill="none"
                            style={{ transform: evidenceOpen ? "rotate(90deg)" : "none", transition: "transform 0.2s" }}
                          >
                            <path d="M4.5 3l3 3-3 3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          {evidenceOpen ? "Hide" : "Show"} attention evidence
                        </button>

                        {evidenceOpen && (
                          <div
                            className="rounded-lg p-3 mb-3 text-xs text-slate-600 leading-relaxed border-l-2"
                            style={{ background: "#f8fafc", borderLeftColor: "#2563EB" }}
                          >
                            <span className="font-medium text-slate-700 block mb-1">Supporting text span:</span>
                            "…{code.supportingEvidence}…"
                          </div>
                        )}

                        {code.userAction === "overridden" && code.overrideReason && (
                          <div
                            className="rounded-lg px-3 py-2 text-xs mb-3"
                            style={{ background: "#fff7ed", color: "#92400e" }}
                          >
                            Override reason: <span className="font-medium">{code.overrideReason}</span>
                          </div>
                        )}

                        {/* Actions */}
                        {!code.userAction && !caseData?.submittedToBilling && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleConfirm(code)}
                              className="flex-1 py-2 rounded-lg text-sm font-medium text-white transition-colors hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-300"
                              style={{ background: "#16A34A" }}
                              aria-label={`Confirm code ${code.code}`}
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => setOverrideModal({ code })}
                              className="flex-1 py-2 rounded-lg text-sm font-medium text-white transition-colors hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-red-300"
                              style={{ background: "#DC2626" }}
                              aria-label={`Override code ${code.code}`}
                            >
                              Override
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Submit bar */}
            <div
              className="flex-shrink-0 px-5 py-4 border-t border-slate-200 bg-white flex items-center justify-between gap-4"
            >
              <div className="text-sm text-slate-600">
                <span className="font-medium text-success">{confirmedCount} confirmed</span>
                {overriddenCount > 0 && (
                  <> · <span className="font-medium text-warning">{overriddenCount} overridden</span></>
                )}
                {pendingCount > 0 && (
                  <> · <span className="text-slate-400">{pendingCount} pending</span></>
                )}
              </div>
              <button
                onClick={() => setConfirmSubmitOpen(true)}
                disabled={!allActioned || !!caseData?.submittedToBilling}
                className="px-5 py-2.5 rounded-lg text-sm font-semibold text-white transition-all focus:outline-none focus:ring-2 focus:ring-blue-300"
                style={{
                  background: allActioned && !caseData?.submittedToBilling ? "#2563EB" : "#cbd5e1",
                  cursor: allActioned && !caseData?.submittedToBilling ? "pointer" : "not-allowed",
                }}
                aria-disabled={!allActioned || !!caseData?.submittedToBilling}
              >
                {caseData?.submittedToBilling
                  ? "✓ Submitted to Billing"
                  : allActioned
                  ? "Submit All Confirmed Codes to Billing"
                  : `Submit to Billing (${pendingCount} pending)`}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Override Modal */}
      {overrideModal && (
        <Modal
          title={`Override Code: ${overrideModal.code.code}`}
          onClose={() => { setOverrideModal(null); setOverrideNewCode(""); setOverrideReason(OVERRIDE_REASONS[0]); }}
          footer={
            <>
              <button
                onClick={() => { setOverrideModal(null); setOverrideNewCode(""); }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 border border-slate-300 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleOverrideSubmit}
                disabled={overrideLoading || !overrideNewCode.trim()}
                className="px-4 py-2 rounded-lg text-sm font-semibold text-white transition"
                style={{ background: overrideLoading || !overrideNewCode.trim() ? "#94a3b8" : "#DC2626" }}
              >
                {overrideLoading ? "Saving…" : "Confirm Override"}
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div className="rounded-lg p-3 text-sm" style={{ background: "#fef3c7", color: "#92400e" }}>
              You are replacing <strong className="font-mono">{overrideModal.code.code}</strong> — {overrideModal.code.description}
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Replacement ICD-10-CM Code <span className="text-danger">*</span>
              </label>
              <input
                type="text"
                value={overrideNewCode}
                onChange={(e) => setOverrideNewCode(e.target.value.toUpperCase())}
                placeholder="e.g. J18.1"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-mono focus:outline-none focus:border-primary focus:ring-2 focus:ring-blue-100"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Override Reason</label>
              <select
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary bg-white"
              >
                {OVERRIDE_REASONS.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
          </div>
        </Modal>
      )}

      {/* Submit Confirmation Modal */}
      {confirmSubmitOpen && (
        <Modal
          title="Submit Codes to Billing"
          onClose={() => setConfirmSubmitOpen(false)}
          footer={
            <>
              <button
                onClick={() => setConfirmSubmitOpen(false)}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 border border-slate-300 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitToBilling}
                disabled={submitLoading}
                className="px-4 py-2 rounded-lg text-sm font-semibold text-white transition"
                style={{ background: submitLoading ? "#93c5fd" : "#2563EB" }}
              >
                {submitLoading ? "Submitting…" : "Confirm Submission"}
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div className="rounded-lg p-4" style={{ background: "#eff6ff", borderLeft: "3px solid #2563EB" }}>
              <p className="text-sm text-slate-700">
                You are about to submit <strong>{confirmedCount + overriddenCount} codes</strong> for case{" "}
                <strong className="font-mono">{caseId}</strong> (Patient <strong>{caseData?.patientId}</strong>) to the billing system.
              </p>
            </div>
            <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 overflow-hidden">
              {codes.map((c) => (
                <div key={c.id} className="flex items-center gap-3 px-3 py-2.5 bg-white">
                  <span
                    className="font-mono text-sm font-semibold"
                    style={{ color: c.userAction === "confirmed" ? "#16A34A" : "#EA580C" }}
                  >
                    {c.userAction === "overridden" && c.overrideCode ? c.overrideCode : c.code}
                  </span>
                  <span className="text-xs text-slate-500 flex-1 truncate">{c.description}</span>
                  <span
                    className="text-xs px-2 py-0.5 rounded-full font-medium"
                    style={{
                      background: c.userAction === "confirmed" ? "#dcfce7" : "#ffedd5",
                      color: c.userAction === "confirmed" ? "#16A34A" : "#EA580C",
                    }}
                  >
                    {c.userAction}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-400">
              This action cannot be undone. All submissions are logged in the audit trail.
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
}
