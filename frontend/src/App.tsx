import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./lib/auth-context";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { LoginPage } from "./pages/LoginPage";
import { HomePage } from "./pages/HomePage";
import { EditorPage } from "./pages/EditorPage";
import { PreviewPage } from "./pages/PreviewPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { TwoFactorVerifyPage } from "./pages/TwoFactorVerifyPage";
import { AccountPage } from "./pages/AccountPage";
import { TwoFactorSetupPage } from "./pages/TwoFactorSetupPage";
import { TwoFactorDisablePage } from "./pages/TwoFactorDisablePage";
import { BackupCodesPage } from "./pages/BackupCodesPage";
import { ComparatorPage } from "./pages/ComparatorPage";
import { AssistantPage } from "./pages/AssistantPage";
import { TemplatesPage } from "./pages/TemplatesPage";
import { HistoryPage } from "./pages/HistoryPage";

export function App() {
  const auth = useAuth();

  if (auth.status === "loading") {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          background: "var(--bg)",
          color: "var(--muted)",
        }}
      >
        Cargando…
      </div>
    );
  }

  if (auth.status === "unauthenticated") {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/two-factor" element={<TwoFactorVerifyPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <>
      <Sidebar />
      <div className="main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/cvs" element={<HomePage />} />
          <Route path="/comparator" element={<ComparatorPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/templates" element={<TemplatesPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/cv/:id" element={<EditorPage />} />
          <Route path="/cv/:id/preview" element={<PreviewPage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/account/2fa/setup" element={<TwoFactorSetupPage />} />
          <Route path="/account/2fa/disable" element={<TwoFactorDisablePage />} />
          <Route path="/account/2fa/backup-codes" element={<BackupCodesPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </>
  );
}
