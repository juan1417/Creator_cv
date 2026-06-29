import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  apiTotpSetupConfirm,
  apiTotpSetupStart,
  type TotpSetupStart,
} from "../lib/api";
import { useAuth } from "../lib/auth-context";

type Stage = "loading" | "scan" | "confirm" | "show_codes" | "error";

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

export function TwoFactorSetupPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [stage, setStage] = useState<Stage>("loading");
  const [setup, setSetup] = useState<TotpSetupStart | null>(null);
  const [code, setCode] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (auth.status !== "authenticated") return;
    apiTotpSetupStart(() => navigate("/login", { replace: true }))
      .then((data) => {
        setSetup(data);
        setStage("scan");
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Error iniciando setup");
        setStage("error");
      });
  }, [auth.status, navigate]);

  if (auth.status !== "authenticated") {
    navigate("/login", { replace: true });
    return null;
  }

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const result = await apiTotpSetupConfirm(code.trim(), () =>
        navigate("/login", { replace: true })
      );
      setBackupCodes(result.backup_codes);
      setStage("show_codes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido");
    }
  };

  if (stage === "loading") {
    return (
      <div className="auth-split">
        <AuthSplit />
        <div className="auth-right">
          <div className="auth-card">
            <div className="auth-card-header">
              <h2>2FA</h2>
              <p>Generando código QR…</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (stage === "error") {
    return (
      <div className="auth-split">
        <AuthSplit />
        <div className="auth-right">
          <div className="auth-card">
            <div className="auth-card-header">
              <h2>2FA</h2>
            </div>
            <div className="flash flash-error" style={{ marginBottom: 16 }}>
              {error}
            </div>
            <Link to="/account" className="btn btn-primary btn-auth">
              Volver
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (stage === "show_codes") {
    return (
      <div className="auth-split">
        <AuthSplit />
        <div className="auth-right">
          <div className="auth-card">
            <div className="auth-card-header">
              <h2>2FA activado</h2>
              <p>Guardá estos códigos en un lugar seguro. Los vas a necesitar si perdés acceso a tu app authenticator.</p>
            </div>

            <div style={{
              background: "var(--bg)",
              borderRadius: "var(--radius)",
              padding: 16,
              marginBottom: 16,
            }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Códigos de respaldo</h3>
              <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
              }}>
                {backupCodes.map((c) => (
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
                Estos códigos no se vuelven a mostrar. Anotalos o imprimilos.
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
      <AuthSplit />
      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-card-header">
            <h2>Configurar 2FA</h2>
            <p>Paso 1: escaneá el QR con tu app authenticator. Paso 2: ingresá el código de 6 dígitos para confirmar.</p>
          </div>

          {setup && (
            <div style={{
              textAlign: "center",
              padding: 20,
              background: "var(--bg)",
              borderRadius: "var(--radius)",
              marginBottom: 16,
            }}>
              <img
                src={setup.qr_data_url}
                alt="QR para 2FA"
                style={{ width: 200, height: 200, margin: "0 auto" }}
              />
              <p style={{
                fontFamily: "var(--mono)",
                fontSize: "0.85rem",
                marginTop: 12,
                wordBreak: "break-all",
                color: "var(--muted)",
              }}>
                {setup.manual_key}
              </p>
              <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
                Si no podés escanear, ingresá esta clave manualmente.
              </p>
            </div>
          )}

          {error && (
            <div className="flash flash-error" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleConfirm}>
            <div className="form-group">
              <label className="form-label" htmlFor="code">Código de la app (6 dígitos)</label>
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
                  setCode(e.target.value.replace(/\s/g, "").slice(0, 6))
                }
                placeholder="123456"
                autoFocus
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-auth"
              disabled={code.length !== 6}
              style={{ marginTop: 8 }}
            >
              Activar 2FA
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
