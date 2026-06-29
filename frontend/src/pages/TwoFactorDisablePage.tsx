import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiTotpDisable } from "../lib/api";
import { useAuth } from "../lib/auth-context";

export function TwoFactorDisablePage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (auth.status !== "authenticated") {
    navigate("/login", { replace: true });
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await apiTotpDisable(password, code.trim(), () =>
        navigate("/login", { replace: true })
      );
      navigate("/account", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo desactivar");
    } finally {
      setSubmitting(false);
    }
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
            <h2>Desactivar 2FA</h2>
            <p>Confirmá tu contraseña y un código actual de tu app authenticator (o un código de respaldo).</p>
          </div>

          {error && (
            <div className="flash flash-error" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="password">Contraseña</label>
              <input
                id="password"
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="code">Código (6 dígitos o XXXX-1234)</label>
              <input
                id="code"
                type="text"
                inputMode="text"
                autoComplete="one-time-code"
                className="form-input"
                style={{
                  letterSpacing: "0.2em",
                  fontFamily: "var(--mono)",
                }}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
              <button
                type="submit"
                className="btn btn-primary btn-auth"
                disabled={submitting || !password || !code}
                style={{ flex: 1 }}
              >
                {submitting ? "Desactivando…" : "Desactivar 2FA"}
              </button>
              <Link to="/account" className="btn btn-secondary btn-auth" style={{ flex: 1 }}>
                Cancelar
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
