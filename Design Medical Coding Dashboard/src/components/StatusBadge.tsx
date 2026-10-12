import type { CaseStatus, VerificationStatus, CodeAction } from "../types";

export function CaseStatusBadge({ status }: { status: CaseStatus }) {
  const styles: Record<CaseStatus, string> = {
    Processing: "bg-blue-100 text-blue-700",
    "Pending Review": "bg-orange-100 text-orange-700",
    Completed: "bg-green-100 text-success",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{
          background:
            status === "Processing" ? "#2563EB" : status === "Pending Review" ? "#EA580C" : "#16A34A",
        }}
      />
      {status}
    </span>
  );
}

export function VerificationBadge({ status }: { status: VerificationStatus }) {
  const styles: Record<VerificationStatus, string> = {
    VERIFIED: "bg-green-100 text-success border border-green-200",
    "PARENT CODE": "bg-blue-100 text-blue-700 border border-blue-200",
    UNVERIFIED: "bg-slate-100 text-slate-600 border border-slate-200",
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold tracking-wide ${styles[status]}`}>
      {status}
    </span>
  );
}

export function ActionBadge({ action }: { action: CodeAction }) {
  const styles: Record<CodeAction, string> = {
    Predicted: "bg-slate-100 text-slate-600",
    Confirmed: "bg-green-100 text-success",
    Overridden: "bg-orange-100 text-warning",
    Submitted: "bg-blue-100 text-primary",
  };
  return (
    <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${styles[action]}`}>
      {action}
    </span>
  );
}
