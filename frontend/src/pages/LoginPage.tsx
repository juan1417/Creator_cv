import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { isPending } from "../lib/api";
import { useAuth } from "../lib/auth-context";

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [pendingVerification, setPendingVerification] = useState<string | null>(null);

  if (auth.status === "authenticated") {
    navigate("/", { replace: true });
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setPendingVerification(null);
    setSubmitting(true);
    try {
      if (isRegister) {
        const result = await auth.signUp(email, password);
        if (result.requires_verification) {
          setPendingVerification(email);
          setPassword("");
        }
      } else {
        const result = await auth.signIn(email, password);
        if (isPending(result)) {
          navigate(
            `/two-factor?pending=${encodeURIComponent(result.pending_token)}`,
            { replace: true }
          );
          return;
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setSubmitting(false);
    }
  };

  if (pendingVerification) {
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
                Te enviamos un enlace de verificación a{" "}
                <strong>{pendingVerification}</strong>.
              </p>
              <p style={{ color: "#6e6e73", fontSize: 14, marginTop: 8 }}>
                Hacé click en el enlace para activar tu cuenta. Si no lo ves, mirá
                en spam o esperá unos minutos.
              </p>
              <button
                className="btn btn-primary btn-auth"
                style={{ marginTop: 24 }}
                onClick={() => {
                  setPendingVerification(null);
                  setIsRegister(false);
                }}
              >
                Volver al inicio
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-split">
      {/* Left panel */}
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

      {/* Right panel */}
      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-card-header">
            <h2>{isRegister ? "Crear cuenta" : "Iniciar sesión"}</h2>
            <p>{isRegister ? "Empieza a crear tu CV profesional" : "Ingresa a tu cuenta para continuar"}</p>
          </div>

          {error && (
            <div className="flash flash-error" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {isRegister && (
              <div className="form-group">
                <label className="form-label">Nombre completo</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="Tu nombre"
                  value={""}
                  readOnly
                  style={{ display: "none" }}
                />
              </div>
            )}

            <div className="form-group">
              <label className="form-label" htmlFor="login-email">Correo electrónico</label>
              <input
                className="form-input"
                type="email"
                id="login-email"
                placeholder="tu@correo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="login-pass">Contraseña</label>
              <input
                className="form-input"
                type="password"
                id="login-pass"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete={isRegister ? "new-password" : "current-password"}
              />
              {isRegister && (
                <div className="form-hint">
                  Mínimo 8 caracteres, una mayúscula y un número.
                </div>
              )}
            </div>

            {!isRegister && (
              <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }}>
                <Link to="/forgot-password" className="btn-ghost" style={{ fontSize: 13 }}>
                  ¿Olvidaste tu contraseña?
                </Link>
              </div>
            )}

            {isRegister && (
              <div style={{ marginBottom: 20 }}>
                <label className="form-check" style={{ margin: 0 }}>
                  <input type="checkbox" required />
                  Acepto los{" "}
                  <a href="#" style={{ color: "var(--accent)", textDecoration: "none" }}>Términos</a>
                  {" "}y{" "}
                  <a href="#" style={{ color: "var(--accent)", textDecoration: "none" }}>Política de privacidad</a>
                </label>
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary btn-auth"
              disabled={submitting}
            >
              {submitting ? "…" : isRegister ? "Crear cuenta" : "Iniciar sesión"}
            </button>
          </form>

          <div className="auth-footer">
            {isRegister ? "¿Ya tienes cuenta?" : "¿No tienes cuenta?"}{" "}
            <button
              className="btn-ghost"
              onClick={() => {
                setIsRegister(!isRegister);
                setError("");
              }}
            >
              {isRegister ? "Iniciar sesión" : "Crear cuenta"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
