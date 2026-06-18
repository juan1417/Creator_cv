import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./lib/auth-context";
import { LoginPage } from "./pages/LoginPage";
import { HomePage } from "./pages/HomePage";
import { EditorPage } from "./pages/EditorPage";
import { PreviewPage } from "./pages/PreviewPage";
import { SiteHeader } from "./components/SiteHeader";

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
          color: "#9a9a9a",
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
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <>
      <SiteHeader />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/cv/:id" element={<EditorPage />} />
        <Route path="/cv/:id/preview" element={<PreviewPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
