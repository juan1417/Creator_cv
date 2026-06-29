import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiBackupCodesRegenerate } from "../lib/api";
import { useAuth } from "../lib/auth-context";

export function BackupCodesPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [codes, setCodes] = useState<string[] | null>(null);
  const [error, setError] = useState("");

  if (auth.status !== "authenticated") {
    navigate("/login", { replace: true });
    return null;
  }

  const handleRegenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await apiBackupCodesRegenerate(password, () =>
        navigate("/login", { replace: true })
      );
      setCodes(result.backup_codes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error regenerando");
    } finally {
      setSubmitting(false);
    }
  };

  if (codes) {
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
              <h2>Códigos de respaldo nuevos</h2>
              <p>Los códigos viejos ya no funcionan. Guardá estos en un lugar seguro.</p>
            </div>

            <div style={{
              background: "var(--bg)",
              borderRadius: "var(--radius)",
              padding: 16,
              marginBottom: 16,
            }}>
              <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
              }}>
                {codes.map((c) => (
                  <div
                    key={c}
                    style={{
                      padding: "8px 12px",
                      background: "#fff",
                      border: "1px solid var(--border)",
                      borderRadius: 4,
                      fontFamily: "var(--mono)",
                      fontSize: "0.9rem",
                      letterSpacing: "0.1em",
                    }}
                  >
                    {c}
                  </div>
                ))}
              </div>
              <p style={{ color: "var(--color-danger-fg)", fontSize: 13, marginTop: 12, fontWeight: 600 }}>
                No se vuelven a mostrar.
              </p>
            </div>

            <Link to="/account" className="btn btn-primary btn-auth">
              Listo
            </Link>
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
            <h2>Regenerar códigos de respaldo</h2>
            <p>Esto invalida los códigos anteriores. Confirmá tu contraseña para continuar.</p>
          </div>

          {error && (
            <div className="flash flash-error" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleRegenerate}>
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
                autoFocus
              />
            </div>

            <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
              <button
                type="submit"
                className="btn btn-primary btn-auth"
                disabled={submitting || !password}
                style={{ flex: 1 }}
              >
                {submitting ? "Regenerando…" : "Regenerar"}
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
