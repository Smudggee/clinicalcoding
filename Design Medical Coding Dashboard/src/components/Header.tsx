import type { AuthState } from "../types";

interface Props {
  auth: AuthState;
  title: string;
  subtitle?: string;
  onSignOut: () => void;
  notificationCount?: number;
}

const roleColors: Record<string, string> = {
  "Medical Coder": "bg-blue-100 text-blue-700",
  Administrator: "bg-purple-100 text-purple-700",
  Physician: "bg-teal-100 text-teal-700",
};

export default function Header({ auth, title, subtitle, onSignOut, notificationCount = 3 }: Props) {
  return (
    <header
      className="flex items-center justify-between px-6 border-b border-slate-200 bg-white"
      style={{ height: 64, minHeight: 64 }}
    >
      <div>
        <h1 className="text-lg font-semibold text-slate-900 leading-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Notification bell */}
        <button
          className="relative text-slate-500 hover:text-slate-700 transition-colors"
          aria-label={`${notificationCount} notifications`}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M10 2a6 6 0 00-6 6c0 3-1 5-1 5h14s-1-2-1-5a6 6 0 00-6-6z"
              stroke="currentColor"
              strokeWidth="1.5"
              fill="none"
            />
            <path d="M8.5 16a1.5 1.5 0 003 0" stroke="currentColor" strokeWidth="1.5" fill="none" />
          </svg>
          {notificationCount > 0 && (
            <span
              className="absolute -top-1 -right-1 flex items-center justify-center rounded-full text-white text-xs font-bold"
              style={{ width: 16, height: 16, background: "#DC2626", fontSize: 10 }}
              aria-hidden="true"
            >
              {notificationCount}
            </span>
          )}
        </button>

        {/* User info */}
        <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
          <div className="text-right">
            <p className="text-sm font-medium text-slate-900 leading-tight">{auth.user.name}</p>
            <span className={`inline-block text-xs px-1.5 py-0.5 rounded font-medium ${roleColors[auth.user.role] ?? "bg-slate-100 text-slate-600"}`}>
              {auth.user.role}
            </span>
          </div>
          <div
            className="flex items-center justify-center rounded-full text-white text-sm font-semibold"
            style={{ width: 36, height: 36, background: "#0B132B", flexShrink: 0 }}
            aria-hidden="true"
          >
            {auth.user.name.charAt(0).toUpperCase()}
          </div>
          <button
            onClick={onSignOut}
            className="text-slate-400 hover:text-danger transition-colors ml-1"
            aria-label="Sign out"
            title="Sign out"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M7 3H3a1 1 0 00-1 1v10a1 1 0 001 1h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M12 6l3 3-3 3M15 9H7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
