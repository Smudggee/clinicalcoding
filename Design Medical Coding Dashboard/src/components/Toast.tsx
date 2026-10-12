import type { Toast } from "../types";

interface Props {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

const icons = {
  success: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="9" fill="#16A34A" />
      <path d="M5 9l3 3 5-5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  error: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="9" fill="#DC2626" />
      <path d="M6 6l6 6M12 6l-6 6" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  warning: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M9 1l8 15H1L9 1z" fill="#EA580C" />
      <path d="M9 7v4M9 13v.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
};

const borderColors = {
  success: "border-l-success",
  error: "border-l-danger",
  warning: "border-l-warning",
};

export default function ToastContainer({ toasts, onRemove }: Props) {
  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="fixed top-4 right-4 z-50 flex flex-col gap-2"
      style={{ maxWidth: 360 }}
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`${t.exiting ? "toast-exit" : "toast-enter"} flex items-start gap-3 bg-white rounded-lg shadow-lg border border-slate-200 border-l-4 ${borderColors[t.type]} p-4`}
          role="alert"
        >
          <span className="flex-shrink-0 mt-0.5">{icons[t.type]}</span>
          <p className="flex-1 text-sm text-slate-800 leading-snug">{t.message}</p>
          <button
            onClick={() => onRemove(t.id)}
            className="flex-shrink-0 text-slate-400 hover:text-slate-600 transition-colors"
            aria-label="Dismiss notification"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}
