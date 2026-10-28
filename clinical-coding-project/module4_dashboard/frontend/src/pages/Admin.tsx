import { useEffect, useState } from "react";
import type { AuthState, SystemSettings } from "../types";
import { MOCK_SYSTEM_USERS, MOCK_CASES } from "../mockData";
import type { SystemUser, Role } from "../types";
import { apiGetSettings, apiUpdateSettings } from "../api";
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
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [threshold, setThreshold] = useState(0.85);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [editUser, setEditUser] = useState<SystemUser | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [newUser, setNewUser] = useState({ name: "", email: "", role: "Medical Coder" as Role });

  useEffect(() => {
    let active = true;
    apiGetSettings()
      .then((loadedSettings) => {
        if (!active) return;
        setSettings(loadedSettings);
        setThreshold(loadedSettings.auto_accept_threshold);
      })
      .catch((error: unknown) => {
        if (active) setSettingsError(error instanceof Error ? error.message : "Could not load backend settings.");
      })
      .finally(() => {
        if (active) setSettingsLoading(false);
      });
    return () => { active = false; };
  }, []);

  async function handleSaveThreshold() {
    if (!settings) return;
    setSettingsSaving(true);
    setSettingsError(null);
    try {
      const updated = await apiUpdateSettings({ ...settings, auto_accept_threshold: threshold });
      setSettings(updated);
      setThreshold(updated.auto_accept_threshold);
      addToast("success", "Auto-accept threshold saved to the backend.");
    } catch (error) {
      setSettingsError(error instanceof Error ? error.message : "Could not save backend settings.");
    } finally {
      setSettingsSaving(false);
    }
  }

  // This preview uses fixture cases only; it does not represent a live workload.
  const demoCasesAboveThreshold = MOCK_CASES.filter((c) =>
    c.predictedCodes.every((p) => p.confidence / 100 >= threshold)
  ).length;
  const demoCasesBelowThreshold = MOCK_CASES.length - demoCasesAboveThreshold;

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
            <div className="border-b border-amber-200 bg-amber-50 px-5 py-3 text-xs text-amber-900" role="status">
              Demo user directory: add, edit, and deactivate actions are local to this browser and do not change sign-in access.
            </div>
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
                This threshold is used by the backend verifier. The counts below use illustrative demo cases only.
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
                  disabled={!settings || settingsLoading || settingsSaving}
                />
                <div className="flex justify-between text-xs text-slate-400 mt-1">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
                <button
                  type="button"
                  onClick={handleSaveThreshold}
                  disabled={!settings || settingsLoading || settingsSaving || threshold === settings?.auto_accept_threshold}
                  className="mt-4 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
                >
                  {settingsLoading ? "Loading settings…" : settingsSaving ? "Saving…" : "Save threshold"}
                </button>
                {settingsError && <p className="mt-2 text-sm text-red-700" role="alert">{settingsError}</p>}
              </div>

              {/* Live preview */}
              <div className="rounded-lg border border-slate-200 overflow-hidden">
                <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
                  <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Illustrative Demo Cases — Preview Only</p>
                </div>
                <div className="grid grid-cols-2 divide-x divide-slate-200">
                  <div className="p-4 text-center">
                    <p className="text-2xl font-bold text-success tabular-nums">{demoCasesAboveThreshold}</p>
                    <p className="text-xs text-slate-500 mt-1">Every sample score meets threshold</p>
                    <p className="text-xs text-slate-400">
                      {MOCK_CASES.length > 0 ? Math.round((demoCasesAboveThreshold / MOCK_CASES.length) * 100) : 0}% of demo cases
                    </p>
                  </div>
                  <div className="p-4 text-center">
                    <p className="text-2xl font-bold text-warning tabular-nums">{demoCasesBelowThreshold}</p>
                    <p className="text-xs text-slate-500 mt-1">Some sample scores below threshold</p>
                    <p className="text-xs text-slate-400">
                      {MOCK_CASES.length > 0 ? Math.round((demoCasesBelowThreshold / MOCK_CASES.length) * 100) : 0}% of demo cases
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
                  { label: "Classifier checkpoint", value: "Not configured", color: "#EA580C" },
                  { label: "Active prediction path", value: "Rule-based demo", color: "#EA580C" },
                  { label: "ICD list", value: "Illustrative sample", color: "#EA580C" },
                  { label: "Classifier inference", value: "Unavailable", color: "#EA580C" },
                  { label: "Case and audit storage", value: "SQLite local database", color: undefined },
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

              <div className="mt-4 rounded-lg p-3 flex items-center gap-2.5" style={{ background: "#fff7ed" }}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" fill="#EA580C" />
                  <path d="M5 8l2.5 2.5L11 5.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div>
                  <p className="text-xs font-semibold text-warning">Demo configuration; classifier unavailable</p>
                  <p className="text-xs text-slate-400">Values describe the current demo configuration.</p>
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
