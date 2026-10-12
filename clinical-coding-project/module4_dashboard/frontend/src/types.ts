export type Role = "Medical Coder" | "Administrator" | "Physician";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  active: boolean;
}

export interface AuthState {
  token: string;
  user: User;
}

export type CaseStatus = "Processing" | "Pending Review" | "Completed";
export type VerificationStatus = "VERIFIED" | "PARENT CODE" | "UNVERIFIED";
export type CodeAction = "Predicted" | "Confirmed" | "Overridden" | "Submitted";

export interface AttentionSpan {
  startIdx: number;
  endIdx: number;
  weight: number;
}

export interface PredictedCode {
  id: string;
  code: string;
  description: string;
  confidence: number; // 0-100
  verificationStatus: VerificationStatus;
  attentionSpans: AttentionSpan[];
  supportingEvidence: string;
  userAction?: "confirmed" | "overridden";
  overrideCode?: string;
  overrideReason?: string;
}

export interface CaseItem {
  id: string;
  patientId: string;
  submittedAt: string;
  status: CaseStatus;
  averageConfidence: number;
  dischargeText: string;
  words: string[];
  predictedCodes: PredictedCode[];
  submittedToBilling?: boolean;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  coderName: string;
  caseId: string;
  action: CodeAction;
  codeAffected: string;
  oldValue: string;
  newValue: string;
}

export interface SystemUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  active: boolean;
  lastLogin: string;
}

export type Page = "signin" | "dashboard" | "case-review" | "audit-trail" | "admin";

export interface Toast {
  id: string;
  type: "success" | "error" | "warning";
  message: string;
  exiting?: boolean;
}

export interface NavigationState {
  page: Page;
  selectedCaseId?: string;
}
