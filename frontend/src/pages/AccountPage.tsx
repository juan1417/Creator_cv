import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth-context";

export function AccountPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  if (auth.status !== "authenticated") {
    navigate("/login", { replace: true });
    return null;
  }

  return (
    <div className="content">
      <div className="topbar" style={{ position: "sticky", top: 0, marginBottom: 0 }}>
        <div className="topbar-left">
          <Link to="/" className="topbar-back" aria-label="Volver al dashboard">←</Link>
          <div className="topbar-title">Mi cuenta</div>
        </div>
      </div>

      <div style={{ maxWidth: 560, padding: "24px 0" }}>
        <div className="section-group">
          <div className="section-group-header">
            <div className="section-group-title">Datos básicos</div>
          </div>
          <div className="section-card">
            <p style={{ color: "var(--muted)", fontSize: 14 }}>
              <strong>Email:</strong> {auth.email}
            </p>
          </div>
        </div>

        <div className="section-group">
          <div className="section-group-header">
            <div className="section-group-title">Seguridad</div>
          </div>
          <div className="section-card">
            <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>
              Verificación en dos pasos (2FA)
            </h3>
            <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 16 }}>
              Agrega una capa extra de seguridad: además de tu contraseña, vas a
              necesitar un código de tu app authenticator para iniciar sesión.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <Link to="/account/2fa/setup" className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}>
                Activar 2FA
              </Link>
              <Link
                to="/account/2fa/disable"
                className="btn btn-secondary"
                style={{ width: "100%", justifyContent: "center" }}
              >
                Desactivar 2FA
              </Link>
              <Link
                to="/account/2fa/backup-codes"
                className="btn btn-ghost"
                style={{ width: "100%", justifyContent: "center" }}
              >
                Regenerar códigos de respaldo
              </Link>
            </div>
          </div>
        </div>

        <div className="section-group">
          <div className="section-group-header">
            <div className="section-group-title">Sesión</div>
          </div>
          <div className="section-card">
            <button
              className="btn btn-secondary"
              style={{ width: "100%", justifyContent: "center" }}
              onClick={() => {
                void auth.signOut().then(() => navigate("/login"));
              }}
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
