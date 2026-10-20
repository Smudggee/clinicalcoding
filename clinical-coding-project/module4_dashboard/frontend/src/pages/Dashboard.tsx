import { useState, useEffect, useCallback } from "react";
import type { AuthState, CaseItem, AuditEntry } from "../types";
import { apiGetCases, apiGetAudit, apiAnalyzeNote } from "../api";
import { CaseStatusBadge } from "../components/StatusBadge";
import { TableRowSkeleton } from "../components/Skeleton";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import Modal from "../components/Modal";
import type { Page } from "../types";

interface Props {
  auth: AuthState;
  onSignOut: () => void;
  onNavigate: (page: Page, caseId?: string) => void;
}

type SortField = "id" | "submittedAt" | "status" | "averageConfidence";
type SortDir = "asc" | "desc";

const PAGE_SIZE = 5;

export default function Dashboard({ auth, onSignOut, onNavigate }: Props) {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<SortField>("submittedAt");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(0);
  const [isAnalyzeOpen, setIsAnalyzeOpen] = useState(false);
  const [customNote, setCustomNote] = useState("");
  const [patientId, setPatientId] = useState("P-9901");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  async function handleAnalyze() {
    if (!customNote.trim()) return;
    setIsAnalyzing(true);
    try {
      const res = await apiAnalyzeNote(customNote, patientId);
      setIsAnalyzeOpen(false);
      setCustomNote("");
      onNavigate("case-review", res.id);
    } catch (e) {
      alert("Analysis failed: " + e);
    } finally {
      setIsAnalyzing(false);
    }
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [c, a] = await Promise.all([apiGetCases(), apiGetAudit()]);
      setCases(c);
      setAudit(a.slice(0, 5));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const sorted = [...cases].sort((a, b) => {
    let av: string | number = a[sortField] ?? "";
    let bv: string | number = b[sortField] ?? "";
    if (sortField === "averageConfidence") { av = Number(av); bv = Number(bv); }
    return sortDir === "asc" ? (av < bv ? -1 : 1) : (av > bv ? -1 : 1);
  });

  const paginated = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);

  function toggleSort(field: SortField) {
    if (sortField === field) setSortDir((d) => d === "asc" ? "desc" : "asc");
    else { setSortField(field); setSortDir("asc"); }
  }

  const SortIcon = ({ field }: { field: SortField }) => (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="inline ml-1 opacity-60">
      {sortField === field ? (
        sortDir === "asc" ? (
          <path d="M6 2l4 6H2l4-6z" fill="currentColor" />
        ) : (
          <path d="M6 10L2 4h8L6 10z" fill="currentColor" />
        )
      ) : (
        <>
          <path d="M6 2l3 4H3l3-4z" fill="currentColor" opacity="0.4" />
          <path d="M6 10L3 6h6L6 10z" fill="currentColor" opacity="0.4" />
        </>
      )}
    </svg>
  );

  const stats = [
    {
      label: "Total cases today",
      value: cases.length,
      icon: "📋",
      color: "#2563EB",
      bg: "#eff6ff",
      trend: "+2",
      up: true,
    },
    {
      label: "Pending review",
      value: cases.filter((c) => c.status === "Pending Review").length,
      icon: "⏳",
      color: "#EA580C",
      bg: "#fff7ed",
      trend: "+1",
      up: false,
    },
    {
      label: "Completed today",
      value: cases.filter((c) => c.status === "Completed").length,
      icon: "✅",
      color: "#16A34A",
      bg: "#f0fdf4",
      trend: "+3",
      up: true,
    },
    {
      label: "Avg. confidence",
      value:
        cases.length > 0
          ? Math.round(cases.reduce((s, c) => s + c.averageConfidence, 0) / cases.length) + "%"
          : "—",
      icon: "🎯",
      color: "#7c3aed",
      bg: "#f5f3ff",
      trend: "+1.2%",
      up: true,
    },
  ];

  function formatTime(iso: string) {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  }

  const actionColors: Record<string, string> = {
    Submitted: "#2563EB",
    Confirmed: "#16A34A",
    Overridden: "#EA580C",
    Predicted: "#64748b",
  };

  return (
    <div className="flex min-h-screen" style={{ background: "#f8fafc" }}>
      <Sidebar currentPage="dashboard" onNavigate={onNavigate} />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          auth={auth}
          title="Dashboard"
          subtitle={new Date().toLocaleDateString("en-GB", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          onSignOut={onSignOut}
        />

        <main className="flex-1 p-6 overflow-auto">
          {/* Stats row */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            {stats.map((s) => (
              <div key={s.label} className="bg-white rounded-xl border border-slate-200 p-5">
                <div className="flex items-start justify-between mb-3">
                  <div
                    className="flex items-center justify-center w-10 h-10 rounded-lg text-lg"
                    style={{ background: s.bg }}
                  >
                    {s.icon}
                  </div>
                  <span
                    className="flex items-center gap-1 text-xs font-medium"
                    style={{ color: s.up ? "#16A34A" : "#DC2626" }}
                  >
                    {s.up ? "▲" : "▼"} {s.trend}
                  </span>
                </div>
                <p className="text-2xl font-bold text-slate-900 tabular-nums">{loading ? "—" : s.value}</p>
                <p className="text-xs text-slate-500 mt-1">{s.label}</p>
              </div>
            ))}
          </div>

          <div className="flex gap-6">
            {/* Main table */}
            <div className="flex-1 bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-900">Pending Cases</h2>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsAnalyzeOpen(true)}
                    className="bg-blue-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-blue-700 transition flex items-center gap-1.5 shadow-sm"
                  >
                    <span>⚡</span> Test My Model (New Note)
                  </button>
                  <button
                    onClick={load}
                    className="text-xs text-primary hover:underline flex items-center gap-1"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M10.5 6a4.5 4.5 0 11-1.5-3.35" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none" />
                      <path d="M9 1v3h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none" />
                    </svg>
                    Refresh
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm" aria-label="Pending cases">
                  <thead>
                    <tr className="border-b border-slate-100" style={{ background: "#f8fafc" }}>
                      {(
                        [
                          ["Case ID", "id"],
                          ["Patient", null],
                          ["Submitted", "submittedAt"],
                          ["Status", "status"],
                          ["Confidence", "averageConfidence"],
                          ["Action", null],
                        ] as [string, SortField | null][]
                      ).map(([label, field]) => (
                        <th
                          key={label}
                          className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide"
                        >
                          {field ? (
                            <button
                              onClick={() => toggleSort(field)}
                              className="flex items-center hover:text-slate-700"
                            >
                              {label}
                              <SortIcon field={field} />
                            </button>
                          ) : (
                            label
                          )}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {loading
                      ? Array.from({ length: 4 }).map((_, i) => (
                          <TableRowSkeleton key={i} cols={6} />
                        ))
                      : paginated.length === 0
                      ? (
                        <tr>
                          <td colSpan={6} className="py-16 text-center">
                            <div className="flex flex-col items-center gap-2 text-slate-400">
                              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                                <circle cx="20" cy="20" r="18" stroke="#e2e8f0" strokeWidth="2" fill="none" />
                                <path d="M13 20h14M20 13v14" stroke="#cbd5e1" strokeWidth="2" strokeLinecap="round" />
                              </svg>
                              <p className="text-sm font-medium text-slate-500">No cases pending</p>
                              <p className="text-xs">All cases have been reviewed or are still processing.</p>
                            </div>
                          </td>
                        </tr>
                      )
                      : paginated.map((c) => (
                        <tr key={c.id} className="table-row-hover">
                          <td className="px-4 py-3">
                            <span className="font-mono text-xs text-slate-700">{c.id}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="font-medium text-slate-800">{c.patientId}</span>
                          </td>
                          <td className="px-4 py-3 text-slate-500 text-xs tabular-nums">
                            {formatTime(c.submittedAt)}
                          </td>
                          <td className="px-4 py-3">
                            <CaseStatusBadge status={c.status} />
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <div
                                className="h-1.5 rounded-full overflow-hidden"
                                style={{ width: 64, background: "#e2e8f0" }}
                              >
                                <div
                                  className="h-full rounded-full"
                                  style={{
                                    width: `${c.averageConfidence}%`,
                                    background:
                                      c.averageConfidence >= 80
                                        ? "#16A34A"
                                        : c.averageConfidence >= 50
                                        ? "#EA580C"
                                        : "#DC2626",
                                  }}
                                />
                              </div>
                              <span className="text-xs tabular-nums text-slate-600">
                                {c.averageConfidence}%
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <button
                              onClick={() => onNavigate("case-review", c.id)}
                              disabled={c.status === "Processing"}
                              className="px-3 py-1.5 rounded-lg text-xs font-medium text-white transition-colors"
                              style={{
                                background: c.status === "Processing" ? "#cbd5e1" : "#2563EB",
                                cursor: c.status === "Processing" ? "not-allowed" : "pointer",
                              }}
                            >
                              {c.status === "Completed" ? "View" : "Review"}
                            </button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {!loading && totalPages > 1 && (
                <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between">
                  <p className="text-xs text-slate-500">
                    Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, sorted.length)} of {sorted.length}
                  </p>
                  <div className="flex gap-1">
                    {Array.from({ length: totalPages }).map((_, i) => (
                      <button
                        key={i}
                        onClick={() => setPage(i)}
                        className="w-7 h-7 rounded text-xs font-medium transition"
                        style={{
                          background: i === page ? "#2563EB" : "transparent",
                          color: i === page ? "white" : "#64748b",
                        }}
                      >
                        {i + 1}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Activity feed */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden" style={{ width: 280, flexShrink: 0 }}>
              <div className="px-5 py-4 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-900">Recent Activity</h2>
              </div>
              <div className="divide-y divide-slate-50">
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="px-4 py-3 flex gap-3">
                      <div className="skeleton w-2 h-2 rounded-full mt-1.5 flex-shrink-0" />
                      <div className="flex-1 space-y-1.5">
                        <div className="skeleton h-3 w-full rounded" />
                        <div className="skeleton h-3 w-2/3 rounded" />
                      </div>
                    </div>
                  ))
                ) : audit.length === 0 ? (
                  <div className="px-4 py-8 text-center text-xs text-slate-400">
                    No recent activity
                  </div>
                ) : (
                  audit.map((a) => (
                    <div key={a.id} className="px-4 py-3 flex gap-3 items-start">
                      <span
                        className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
                        style={{ background: actionColors[a.action] ?? "#94a3b8" }}
                      />
                      <div className="min-w-0">
                        <p className="text-xs text-slate-800 leading-snug">
                          <span className="font-medium">{a.coderName}</span>{" "}
                          <span style={{ color: actionColors[a.action] }}>{a.action.toLowerCase()}</span>{" "}
                          <span className="font-mono">{a.codeAffected}</span>
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {a.caseId} · {new Date(a.timestamp).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="px-4 py-3 border-t border-slate-100">
                <button
                  onClick={() => onNavigate("audit-trail")}
                  className="text-xs text-primary hover:underline"
                >
                  View full audit trail →
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>

      {isAnalyzeOpen && (
        <Modal
          title="⚡ Test Person 2's Bio_ClinicalBERT Model"
          wide
          onClose={() => setIsAnalyzeOpen(false)}
          footer={
            <>
              <button
                type="button"
                onClick={() => setIsAnalyzeOpen(false)}
                className="px-4 py-2 border border-slate-200 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isAnalyzing || !customNote.trim()}
                onClick={handleAnalyze}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <span className="animate-spin text-base">⏳</span> Running Transformer...
                  </>
                ) : (
                  "Predict ICD-10 Codes →"
                )}
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Patient Identifier
              </label>
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="w-full text-sm border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. P-8042"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-700">
                  Clinical Discharge Note / Summary
                </label>
                <span className="text-xs text-slate-400">Quick fill sample:</span>
              </div>
              <div className="flex gap-2 mb-2">
                <button
                  type="button"
                  onClick={() =>
                    setCustomNote(
                      "Patient is a 68-year-old male presenting with acute crushing chest pain radiating to left jaw. ECG confirms acute anterior ST-elevation myocardial infarction (STEMI). History of essential primary hypertension and poorly controlled type 2 diabetes mellitus without complications. Started on dual antiplatelet therapy and emergency catheterization."
                    )
                  }
                  className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded border border-slate-200"
                >
                  Heart Attack + HTN
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setCustomNote(
                      "Patient with severe COPD acute exacerbation presenting with purulent productive cough, fever of 38.8C, and hypoxia requiring 3L nasal cannula. History of chronic kidney disease stage 3. Administered IV antibiotics, nebulized bronchodilators, and systemic steroids."
                    )
                  }
                  className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded border border-slate-200"
                >
                  COPD Exacerbation + CKD
                </button>
              </div>
              <textarea
                rows={7}
                value={customNote}
                onChange={(e) => setCustomNote(e.target.value)}
                placeholder="Type or paste any clinical note here..."
                className="w-full text-sm font-sans border border-slate-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="text-xs text-slate-500 bg-blue-50 p-2.5 rounded-lg border border-blue-100">
              💡 <b>Under the hood:</b> This note will be split via Person 1's sliding window (512 tokens, 256 stride), passed to your <b>Bio_ClinicalBERT Transformer</b> for multi-label inference, aggregated via max-pooling, verified by Person 3, and visualized on the HITL review screen!
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
}
