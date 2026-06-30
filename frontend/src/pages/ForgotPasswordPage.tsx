import { useState } from "react";
import { Link } from "react-router-dom";
import { apiForgotPassword } from "../lib/api";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await apiForgotPassword(email);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setSubmitting(false);
    }
  };

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
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
              </div>
              <h3>Revisá tu email</h3>
              <p>
                Si la dirección <strong>{email}</strong> está registrada, te enviamos
                un enlace para restablecer la contraseña.
              </p>
              <p style={{ color: "#6e6e73", fontSize: 14, marginTop: 8 }}>
                El enlace expira en 1 hora. Si no ves el mensaje, mirá en spam.
              </p>
              <Link to="/login" className="btn btn-primary btn-auth" style={{ marginTop: 24 }}>
                Volver al inicio de sesión
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
            <h2>Restablecer contraseña</h2>
            <p>Ingresá tu email y te enviaremos un enlace para crear una contraseña nueva.</p>
          </div>

          {error && (
            <div className="flash flash-error" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="email">Correo electrónico</label>
              <input
                className="form-input"
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
                autoComplete="email"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-auth"
              disabled={submitting}
              style={{ marginTop: 8 }}
            >
              {submitting ? "Enviando…" : "Enviar enlace"}
            </button>
          </form>

          <div className="auth-footer">
            <Link to="/login">Volver al inicio de sesión</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
