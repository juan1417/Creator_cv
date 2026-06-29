import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiResetPassword } from "../lib/api";

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = useMemo(() => params.get("token") ?? "", [params]);

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  if (!token) {
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
              <h2>Enlace inválido</h2>
              <p>No se encontró el token de reseteo. Solicitá uno nuevo.</p>
            </div>
            <button className="btn btn-primary btn-auth" onClick={() => navigate("/forgot-password")}>
              Solicitar enlace nuevo
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (done) {
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
            <div className="auth-success">
              <div className="auth-success-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
              </div>
              <h3>Contraseña actualizada</h3>
              <p>Ya podés iniciar sesión con tu nueva contraseña.</p>
              <button className="btn btn-primary btn-auth" style={{ marginTop: 24 }} onClick={() => navigate("/login")}>
                Ir al inicio de sesión
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres.");
      return;
    }
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setSubmitting(true);
    try {
      await apiResetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
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
            <h2>Nueva contraseña</h2>
            <p>Elegí una contraseña segura para tu cuenta.</p>
          </div>

          {error && (
            <div className="flash flash-error" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="password">Nueva contraseña (mínimo 6 caracteres)</label>
              <input
                className="form-input"
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoFocus
                autoComplete="new-password"
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="confirm">Confirmar contraseña</label>
              <input
                className="form-input"
                type="password"
                id="confirm"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-auth"
              disabled={submitting}
              style={{ marginTop: 8 }}
            >
              {submitting ? "Guardando…" : "Cambiar contraseña"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
