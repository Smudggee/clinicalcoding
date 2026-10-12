import type { Page } from "../types";

interface Props {
  currentPage: Page;
  onNavigate: (page: Page) => void;
}

const navItems: { page: Page; label: string; icon: React.ReactNode }[] = [
  {
    page: "dashboard",
    label: "Dashboard",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="2" y="2" width="7" height="7" rx="1.5" fill="currentColor" />
        <rect x="11" y="2" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.6" />
        <rect x="2" y="11" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.6" />
        <rect x="11" y="11" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.4" />
      </svg>
    ),
  },
  {
    page: "case-review",
    label: "Pending Cases",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path
          d="M4 3h8l4 4v10a1 1 0 01-1 1H4a1 1 0 01-1-1V4a1 1 0 011-1z"
          stroke="currentColor"
          strokeWidth="1.5"
          fill="none"
        />
        <path d="M12 3v4h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M7 10h6M7 13h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    page: "audit-trail",
    label: "Audit Trail",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path
          d="M10 2a8 8 0 100 16A8 8 0 0010 2z"
          stroke="currentColor"
          strokeWidth="1.5"
          fill="none"
        />
        <path d="M10 6v4l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    page: "admin",
    label: "Settings",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="3" stroke="currentColor" strokeWidth="1.5" fill="none" />
        <path
          d="M10 2v2M10 16v2M2 10h2M16 10h2M4.22 4.22l1.42 1.42M14.36 14.36l1.42 1.42M4.22 15.78l1.42-1.42M14.36 5.64l1.42-1.42"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    ),
  },
];

export default function Sidebar({ currentPage, onNavigate }: Props) {
  return (
    <aside
      className="sidebar-scroll flex flex-col"
      style={{
        width: 64,
        minWidth: 64,
        background: "#0B132B",
        height: "100vh",
        position: "sticky",
        top: 0,
        overflowY: "auto",
      }}
      aria-label="Main navigation"
    >
      {/* Logo mark */}
      <div className="flex items-center justify-center h-16 border-b" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
        <div
          className="flex items-center justify-center rounded-lg"
          style={{ width: 36, height: 36, background: "#2563EB" }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 3v14M3 10h14" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex flex-col items-center gap-1 py-4 flex-1">
        {navItems.map((item) => {
          const isActive = currentPage === item.page ||
            (item.page === "case-review" && currentPage === "case-review");
          return (
            <button
              key={item.page}
              onClick={() => onNavigate(item.page)}
              title={item.label}
              aria-label={item.label}
              aria-current={isActive ? "page" : undefined}
              className="relative group flex items-center justify-center rounded-lg transition-all"
              style={{
                width: 44,
                height: 44,
                color: isActive ? "#ffffff" : "rgba(255,255,255,0.45)",
                background: isActive ? "rgba(37,99,235,0.3)" : "transparent",
              }}
              onMouseEnter={(e) => {
                if (!isActive) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.08)";
              }}
              onMouseLeave={(e) => {
                if (!isActive) (e.currentTarget as HTMLElement).style.background = "transparent";
              }}
            >
              {item.icon}
              {isActive && (
                <span
                  className="absolute right-0 top-1/2 -translate-y-1/2 w-0.5 rounded-full"
                  style={{ height: 24, background: "#2563EB" }}
                />
              )}
              {/* Tooltip */}
              <span
                className="absolute left-14 px-2 py-1 rounded text-xs font-medium whitespace-nowrap pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity z-50"
                style={{ background: "#1a2744", color: "white" }}
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
