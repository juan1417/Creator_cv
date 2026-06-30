import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../lib/auth-context";

export function TwoFactorVerifyPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const pending = params.get("pending") ?? "";

  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (auth.status === "authenticated") {
    navigate("/", { replace: true });
    return null;
  }

  if (!pending) {
    return (
      <div className="auth-split">
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
        <div className="auth-right">
          <div className="auth-card">
            <div className="auth-card-header">
              <h2>Sesión inválida</h2>
              <p>Volvé a iniciar sesión para volver a intentar la verificación.</p>
            </div>
            <button className="btn btn-primary btn-auth" onClick={() => navigate("/login")}>
              Iniciar sesión
            </button>
          </div>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await auth.verifyTwoFactor(pending, code.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido");
    } finally {
      setSubmitting(false);
    }
  };

  const handleBackupCode = async () => {
    await handleSubmit({ preventDefault: () => {} } as React.FormEvent);
  };

  return (
    <div className="auth-split">
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
      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-card-header">
            <h2>Verificación en dos pasos</h2>
            <p>Abrí tu app authenticator (Google Authenticator, Authy, 1Password…) e ingresá el código de 6 dígitos.</p>
          </div>

          {error && (
            <div className="flash flash-error" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="code">Código</label>
              <input
                id="code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                className="form-input"
                style={{
                  letterSpacing: "0.3em",
                  fontFamily: "var(--mono)",
                  fontSize: "1.4rem",
                  textAlign: "center",
                }}
                value={code}
                onChange={(e) =>
                  setCode(e.target.value.replace(/\s/g, "").slice(0, 9))
                }
                placeholder="123 456"
                autoFocus
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-auth"
              disabled={submitting || !code}
              style={{ marginTop: 8 }}
            >
              {submitting ? "Verificando…" : "Verificar"}
            </button>
          </form>

          <div className="auth-footer">
            ¿Perdiste el acceso? Ingresá un{" "}
            <button
              className="btn-ghost"
              onClick={handleBackupCode}
            >
              código de respaldo
            </button>{" "}
            (XXXX-1234).
          </div>
        </div>
      </div>
    </div>
  );
}
