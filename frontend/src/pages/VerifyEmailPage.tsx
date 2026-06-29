import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../lib/auth-context";

type Status = "verifying" | "success" | "error";

function AuthSplit() {
  return (
    <>
      <div className="auth-left">
        <div className="auth-brand">Creator CV</div>
        <div className="auth-circle auth-circle-1" />
        <div className="auth-circle auth-circle-2" />
        <div className="auth-circle auth-circle-3" />
        <div className="auth-left-content">
          <h1>Crea tu CV perfecto</h1>
          <p>Asistido por inteligencia artificial. Compara con ofertas reales y obtén un puntaje de compatibilidad.</p>
          <div className="accent-line" />
        </div>
      </div>
    </>
  );
}

export function VerifyEmailPage() {
  const auth = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const [status, setStatus] = useState<Status>(token ? "verifying" : "error");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        await auth.verifyEmail(token);
        if (!cancelled) setStatus("success");
      } catch (err) {
        if (cancelled) return;
        setStatus("error");
        setErrorMsg(err instanceof Error ? err.message : "Enlace inválido");
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (auth.status === "authenticated" && status !== "success") {
    return (
      <div className="auth-split">
        <AuthSplit />
        <div className="auth-right">
          <div className="auth-card">
            <div className="auth-card-header">
              <h2>Cuenta activa</h2>
              <p>Tu cuenta ya está verificada.</p>
            </div>
            <button className="btn btn-primary btn-auth" onClick={() => navigate("/")}>
              Ir al inicio
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-split">
      <AuthSplit />
      <div className="auth-right">
        <div className="auth-card">
          {status === "verifying" && (
            <>
              <div className="auth-card-header">
                <h2>Verificando…</h2>
                <p>Activando tu cuenta.</p>
              </div>
            </>
          )}
          {status === "success" && (
            <>
              <div className="auth-success">
                <div className="auth-success-icon">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                </div>
                <h3>¡Listo!</h3>
                <p>Tu cuenta está verificada. Ya podés empezar a crear tus CVs.</p>
                <button className="btn btn-primary btn-auth" style={{ marginTop: 24 }} onClick={() => navigate("/")}>
                  Empezar
                </button>
              </div>
            </>
          )}
          {status === "error" && (
            <>
              <div className="auth-card-header">
                <h2>No se pudo verificar</h2>
                <p>{errorMsg || "El enlace no es válido."}</p>
              </div>
              <button className="btn btn-primary btn-auth" onClick={() => navigate("/login")}>
                Volver al inicio de sesión
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
