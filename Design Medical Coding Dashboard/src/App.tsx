import { useState, useCallback } from "react";
import type { AuthState, NavigationState, Page } from "./types";
import { setToken } from "./api";
import { useToast } from "./hooks/useToast";
import ToastContainer from "./components/Toast";
import SignIn from "./pages/SignIn";
import Dashboard from "./pages/Dashboard";
import CaseReview from "./pages/CaseReview";
import AuditTrail from "./pages/AuditTrail";
import Admin from "./pages/Admin";

export default function App() {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [nav, setNav] = useState<NavigationState>({ page: "signin" });
  const { toasts, addToast, removeToast } = useToast();

  const navigate = useCallback((page: Page, caseId?: string) => {
    setNav({ page, selectedCaseId: caseId });
  }, []);

  function handleSignIn(a: AuthState) {
    setAuth(a);
    setToken(a.token);
    setNav({ page: "dashboard" });
    addToast("success", `Welcome back, ${a.user.name}.`);
  }

  function handleSignOut() {
    setAuth(null);
    setToken(null);
    setNav({ page: "signin" });
  }

  if (!auth || nav.page === "signin") {
    return (
      <>
        <SignIn onSignIn={handleSignIn} />
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </>
    );
  }

  return (
    <>
      {(nav.page === "dashboard" || (!["case-review", "audit-trail", "admin"].includes(nav.page))) && (
        <Dashboard auth={auth} onSignOut={handleSignOut} onNavigate={navigate} />
      )}
      {nav.page === "case-review" && nav.selectedCaseId && (
        <CaseReview
          auth={auth}
          caseId={nav.selectedCaseId}
          onSignOut={handleSignOut}
          onNavigate={navigate}
          addToast={addToast}
        />
      )}
      {nav.page === "case-review" && !nav.selectedCaseId && (
        // No case selected — go to dashboard and pick one
        <Dashboard auth={auth} onSignOut={handleSignOut} onNavigate={navigate} />
      )}
      {nav.page === "audit-trail" && (
        <AuditTrail auth={auth} onSignOut={handleSignOut} onNavigate={navigate} />
      )}
      {nav.page === "admin" && (
        <Admin auth={auth} onSignOut={handleSignOut} onNavigate={navigate} addToast={addToast} />
      )}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </>
  );
}
