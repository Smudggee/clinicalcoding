import { useState } from "react";
import type { AuthState } from "../types";
import { MOCK_SYSTEM_USERS, MOCK_CASES } from "../mockData";
import type { SystemUser, Role } from "../types";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import Modal from "../components/Modal";
import type { Page, Toast } from "../types";

interface Props {
  auth: AuthState;
  onSignOut: () => void;
  onNavigate: (page: Page) => void;
  addToast: (type: Toast["type"], message: string) => void;
}

const ALL_ROLES: Role[] = ["Medical Coder", "Administrator", "Physician"];
const roleColors: Record<Role, string> = {
  "Medical Coder": "bg-blue-100 text-blue-700",
  Administrator: "bg-purple-100 text-purple-700",
  Physician: "bg-teal-100 text-teal-700",
};

export default function Admin({ auth, onSignOut, onNavigate, addToast }: Props) {
  const [users, setUsers] = useState<SystemUser[]>(MOCK_SYSTEM_USERS);
  const [threshold, setThreshold] = useState(0.8);
  const [editUser, setEditUser] = useState<SystemUser | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [newUser, setNewUser] = useState({ name: "", email: "", role: "Medical Coder" as Role });

  // Compute auto-commit preview
  const autoCommitCount = MOCK_CASES.filter((c) =>
    c.predictedCodes.every((p) => p.confidence / 100 >= threshold)
  ).length;
  const reviewCount = MOCK_CASES.length - autoCommitCount;

  function handleToggleActive(userId: string) {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, active: !u.active } : u))
    );
    const user = users.find((u) => u.id === userId);
    addToast("success", `${user?.name} has been ${user?.active ? "deactivated" : "reactivated"}.`);
  }

  function handleEditSave() {
    if (!editUser) return;
    setUsers((prev) => prev.map((u) => (u.id === editUser.id ? editUser : u)));
    addToast("success", `${editUser.name}'s profile updated.`);
    setEditUser(null);
  }

  function handleAddUser() {
    if (!newUser.name || !newUser.email) {
      addToast("warning", "Name and email are required.");
      return;
    }
    const user: SystemUser = {
      id: `usr-${Date.now()}`,
      name: newUser.name,
      email: newUser.email,
      role: newUser.role,
      active: true,
      lastLogin: "—",
    };
    setUsers((prev) => [...prev, user]);
    addToast("success", `User ${newUser.name} added.`);
    setAddOpen(false);
    setNewUser({ name: "", email: "", role: "Medical Coder" });
  }

  function formatLastLogin(s: string) {
    if (s === "—") return "Never";
    return new Date(s).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  }

  return (
    <div className="flex min-h-screen" style={{ background: "#f8fafc" }}>
      <Sidebar currentPage="admin" onNavigate={onNavigate} />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          auth={auth}
          title="Administrator"
          subtitle="User management, thresholds, and system health"
          onSignOut={onSignOut}
        />

        <main className="flex-1 p-6 overflow-auto space-y-6">
          {/* User Management */}
          <section className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">User Management</h2>
                <p className="text-xs text-slate-400 mt-0.5">{users.filter((u) => u.active).length} active users</p>
              </div>
              <button
                onClick={() => setAddOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white"
                style={{ background: "#2563EB" }}
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 2v8M2 6h8" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                Add User
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm" aria-label="User management">
                <thead>
                  <tr className="border-b border-slate-100" style={{ background: "#f8fafc" }}>
                    {["User", "Email", "Role", "Last Login", "Status", "Actions"].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {users.map((u) => (
                    <tr key={u.id} className="table-row-hover">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <div
                            className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                            style={{ background: u.active ? "#0B132B" : "#94a3b8" }}
                          >
                            {u.name.charAt(0)}
                          </div>
                          <span className="font-medium text-slate-800">{u.name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs">{u.email}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${roleColors[u.role]}`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 tabular-nums">
                        {formatLastLogin(u.lastLogin)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${u.active ? "bg-green-100 text-success" : "bg-slate-100 text-slate-500"}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${u.active ? "bg-success" : "bg-slate-400"}`} />
                          {u.active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditUser({ ...u })}
                            className="px-2.5 py-1 rounded text-xs font-medium text-slate-600 border border-slate-300 hover:bg-slate-50 transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleToggleActive(u.id)}
                            className="px-2.5 py-1 rounded text-xs font-medium transition border"
                            style={{
                              color: u.active ? "#DC2626" : "#16A34A",
                              borderColor: u.active ? "#fecaca" : "#bbf7d0",
                              background: u.active ? "#fff0f0" : "#f0fdf4",
                            }}
                          >
                            {u.active ? "Deactivate" : "Reactivate"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="grid grid-cols-2 gap-6">
            {/* Confidence Threshold */}
            <section className="bg-white rounded-xl border border-slate-200 p-5">
              <h2 className="text-sm font-semibold text-slate-900 mb-1">Confidence Threshold</h2>
              <p className="text-xs text-slate-400 mb-5">
                Cases where all codes exceed this threshold auto-commit without coder review.
              </p>
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-slate-600">Global threshold</span>
                  <span
                    className="text-2xl font-bold tabular-nums"
                    style={{ color: threshold >= 0.8 ? "#16A34A" : threshold >= 0.5 ? "#EA580C" : "#DC2626" }}
                  >
                    {(threshold * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))}
                  className="w-full accent-primary"
                  aria-label="Confidence threshold"
                />
                <div className="flex justify-between text-xs text-slate-400 mt-1">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>

              {/* Live preview */}
              <div className="rounded-lg border border-slate-200 overflow-hidden">
                <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
                  <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Live Preview — Today's Cases</p>
                </div>
                <div className="grid grid-cols-2 divide-x divide-slate-200">
                  <div className="p-4 text-center">
                    <p className="text-2xl font-bold text-success tabular-nums">{autoCommitCount}</p>
                    <p className="text-xs text-slate-500 mt-1">Auto-commit</p>
                    <p className="text-xs text-slate-400">
                      {MOCK_CASES.length > 0 ? Math.round((autoCommitCount / MOCK_CASES.length) * 100) : 0}% of cases
                    </p>
                  </div>
                  <div className="p-4 text-center">
                    <p className="text-2xl font-bold text-warning tabular-nums">{reviewCount}</p>
                    <p className="text-xs text-slate-500 mt-1">Go to review</p>
                    <p className="text-xs text-slate-400">
                      {MOCK_CASES.length > 0 ? Math.round((reviewCount / MOCK_CASES.length) * 100) : 0}% of cases
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* System Health */}
            <section className="bg-white rounded-xl border border-slate-200 p-5">
              <h2 className="text-sm font-semibold text-slate-900 mb-4">System Health</h2>
              <div className="space-y-3">
                {[
                  { label: "BioBERT Model Version", value: "v2.1.3", color: "#16A34A" },
                  { label: "ICD-10-CM Ontology", value: "2024.2 (FY2025)", color: "#16A34A" },
                  { label: "Last Model Update", value: "1 Sep 2026", color: undefined },
                  { label: "Avg. Inference Latency", value: "124 ms", color: "#16A34A" },
                  { label: "Cases Processed Today", value: "47", color: undefined },
                  { label: "Queue Depth", value: "3 pending", color: "#EA580C" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                    <span className="text-xs text-slate-500">{item.label}</span>
                    <span
                      className="text-sm font-semibold tabular-nums"
                      style={{ color: item.color ?? "#1e293b" }}
                    >
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>

              <div className="mt-4 rounded-lg p-3 flex items-center gap-2.5" style={{ background: "#f0fdf4" }}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" fill="#16A34A" />
                  <path d="M5 8l2.5 2.5L11 5.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div>
                  <p className="text-xs font-semibold text-success">All systems operational</p>
                  <p className="text-xs text-slate-400">Last health check: 2 minutes ago</p>
                </div>
              </div>
            </section>
          </div>
        </main>
      </div>

      {/* Edit User Modal */}
      {editUser && (
        <Modal
          title={`Edit User — ${editUser.name}`}
          onClose={() => setEditUser(null)}
          footer={
            <>
              <button onClick={() => setEditUser(null)} className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 border border-slate-300 hover:bg-slate-50 transition">
                Cancel
              </button>
              <button onClick={handleEditSave} className="px-4 py-2 rounded-lg text-sm font-semibold text-white" style={{ background: "#2563EB" }}>
                Save Changes
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Full Name</label>
              <input
                type="text"
                value={editUser.name}
                onChange={(e) => setEditUser({ ...editUser, name: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
              <input
                type="email"
                value={editUser.email}
                onChange={(e) => setEditUser({ ...editUser, email: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Role</label>
              <select
                value={editUser.role}
                onChange={(e) => setEditUser({ ...editUser, role: e.target.value as Role })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary bg-white"
              >
                {ALL_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
        </Modal>
      )}

      {/* Add User Modal */}
      {addOpen && (
        <Modal
          title="Add New User"
          onClose={() => { setAddOpen(false); setNewUser({ name: "", email: "", role: "Medical Coder" }); }}
          footer={
            <>
              <button onClick={() => setAddOpen(false)} className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 border border-slate-300 hover:bg-slate-50 transition">
                Cancel
              </button>
              <button onClick={handleAddUser} className="px-4 py-2 rounded-lg text-sm font-semibold text-white" style={{ background: "#2563EB" }}>
                Add User
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Full Name <span className="text-danger">*</span></label>
              <input
                type="text"
                value={newUser.name}
                onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                placeholder="e.g. Dr. Jane Smith"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Email <span className="text-danger">*</span></label>
              <input
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                placeholder="e.g. j.smith@hospital.org"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Role</label>
              <select
                value={newUser.role}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value as Role })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary bg-white"
              >
                {ALL_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
