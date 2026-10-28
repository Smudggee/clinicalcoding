import { useState, useEffect, useCallback } from "react";
import type { AuthState, AuditEntry } from "../types";
import { apiGetAudit } from "../api";
import { ActionBadge } from "../components/StatusBadge";
import { TableRowSkeleton } from "../components/Skeleton";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import type { Page } from "../types";

interface Props {
  auth: AuthState;
  onSignOut: () => void;
  onNavigate: (page: Page, caseId?: string) => void;
}

const PAGE_SIZE = 10;

export default function AuditTrail({ auth, onSignOut, onNavigate }: Props) {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterCaseId, setFilterCaseId] = useState("");
  const [filterFrom, setFilterFrom] = useState("");
  const [filterTo, setFilterTo] = useState("");
  const [filterAction, setFilterAction] = useState("");
  const [page, setPage] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGetAudit({
        caseId: filterCaseId || undefined,
        from: filterFrom || undefined,
        to: filterTo || undefined,
      });
      setEntries(data);
      setPage(0);
    } finally {
      setLoading(false);
    }
  }, [filterCaseId, filterFrom, filterTo]);

  useEffect(() => { load(); }, [load]);

  const filtered = filterAction
    ? entries.filter((e) => e.action === filterAction)
    : entries;

  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

  function exportCSV() {
    const header = "Timestamp,Actor,Case ID,Action,Code,Old Value,New Value";
    const rows = filtered.map((e) =>
      [e.timestamp, `"${e.coderName}"`, e.caseId, e.action, `"${e.codeAffected}"`, `"${e.oldValue}"`, `"${e.newValue}"`].join(",")
    );
    const blob = new Blob([[header, ...rows].join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-trail-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function formatDateTime(iso: string) {
    const d = new Date(iso);
    return d.toLocaleString("en-GB", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  }

  return (
    <div className="flex min-h-screen" style={{ background: "#f8fafc" }}>
      <Sidebar currentPage="audit-trail" onNavigate={onNavigate} />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          auth={auth}
          title="Audit Trail"
          subtitle="Read-only record of all coding actions"
          onSignOut={onSignOut}
        />

        <main className="flex-1 p-6 overflow-auto">
          {!loading && entries.some((entry) => entry.dataSource === "mock") && (
            <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900" role="status">
              Demo mode: these audit entries are local browser data and are not saved in the backend.
            </div>
          )}
          {!loading && entries.some((entry) => entry.dataSource === "backend") && (
            <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900" role="status">
              These audit entries were loaded from the backend.
            </div>
          )}
          {/* Filters */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
            <div className="flex items-end gap-4 flex-wrap">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Case ID</label>
                <input
                  type="text"
                  value={filterCaseId}
                  onChange={(e) => setFilterCaseId(e.target.value)}
                  placeholder="e.g. CASE-2024-0831"
                  className="px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-blue-100"
                  style={{ width: 200 }}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">From date</label>
                <input
                  type="date"
                  value={filterFrom}
                  onChange={(e) => setFilterFrom(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">To date</label>
                <input
                  type="date"
                  value={filterTo}
                  onChange={(e) => setFilterTo(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Action type</label>
                <select
                  value={filterAction}
                  onChange={(e) => setFilterAction(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary bg-white"
                  style={{ width: 160 }}
                >
                  <option value="">All actions</option>
                  {["Predicted", "Confirmed", "Overridden", "Rejected", "Submitted"].map((a) => (
                    <option key={a} value={a}>{a}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={load}
                className="px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors"
                style={{ background: "#2563EB" }}
              >
                Apply Filters
              </button>
              <button
                onClick={() => {
                  setFilterCaseId("");
                  setFilterFrom("");
                  setFilterTo("");
                  setFilterAction("");
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 border border-slate-300 hover:bg-slate-50 transition"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Audit Log</h2>
                {!loading && (
                  <p className="text-xs text-slate-400 mt-0.5">{filtered.length} entries</p>
                )}
              </div>
              <button
                onClick={exportCSV}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 border border-slate-300 hover:bg-slate-50 transition"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M7 2v7M4 7l3 3 3-3M2 11h10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Export CSV
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm" aria-label="Audit trail">
                <thead>
                  <tr className="border-b border-slate-100" style={{ background: "#f8fafc" }}>
                    {["Timestamp", "Actor", "Case ID", "Action", "Code Affected", "Old Value", "New Value"].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {loading ? (
                    Array.from({ length: 6 }).map((_, i) => <TableRowSkeleton key={i} cols={7} />)
                  ) : paginated.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-16 text-center">
                        <div className="flex flex-col items-center gap-2 text-slate-400">
                          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                            <circle cx="20" cy="20" r="18" stroke="#e2e8f0" strokeWidth="2" fill="none" />
                            <path d="M13 28l5-8 4 6 3-4 5 6" stroke="#cbd5e1" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          <p className="text-sm font-medium text-slate-500">No audit entries found</p>
                          <p className="text-xs">Try adjusting your filters.</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    paginated.map((e) => (
                      <tr key={e.id} className="table-row-hover">
                        <td className="px-4 py-3 text-xs tabular-nums text-slate-500 whitespace-nowrap">
                          {formatDateTime(e.timestamp)}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm font-medium text-slate-800">{e.coderName}</span>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => {
                              if (e.caseId !== "ALL") onNavigate("case-review", e.caseId);
                            }}
                            className="font-mono text-xs text-primary hover:underline"
                          >
                            {e.caseId}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          <ActionBadge action={e.action} />
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-slate-700">{e.codeAffected}</td>
                        <td className="px-4 py-3 text-xs text-slate-500">{e.oldValue}</td>
                        <td className="px-4 py-3 text-xs text-slate-700">{e.newValue}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {!loading && totalPages > 1 && (
              <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between">
                <p className="text-xs text-slate-500">
                  Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}
                </p>
                <div className="flex gap-1">
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="px-3 py-1.5 rounded text-xs font-medium text-slate-600 border border-slate-300 disabled:opacity-40 hover:bg-slate-50 transition"
                  >
                    ‹ Prev
                  </button>
                  <span className="px-3 py-1.5 text-xs text-slate-500 tabular-nums">
                    {page + 1} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                    disabled={page >= totalPages - 1}
                    className="px-3 py-1.5 rounded text-xs font-medium text-slate-600 border border-slate-300 disabled:opacity-40 hover:bg-slate-50 transition"
                  >
                    Next ›
                  </button>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
