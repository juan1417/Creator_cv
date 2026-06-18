import { useState } from "react";
import { supabase } from "../lib/supabase";
import { useAuth } from "../lib/auth-context";

export function LoginPage() {
  const auth = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");

  if (auth.status === "authenticated") {
    window.location.href = "/";
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const { error: err } = isRegister
      ? await supabase.auth.signUp({ email, password })
      : await supabase.auth.signInWithPassword({ email, password });

    if (err) {
      setError(err.message);
    }
  };

  return (
    <div className="wrap" style={{ maxWidth: 400, marginTop: 80 }}>
      <h1 style={{ marginBottom: 24, textAlign: "center" }}>Creator CV</h1>

      <div className="card">
        <h2 style={{ marginBottom: 20 }}>
          {isRegister ? "Crear cuenta" : "Iniciar sesión"}
        </h2>

        {error && (
          <div className="flash flash-error" style={{ marginBottom: 16 }}>
            {error}
          </div>
        )}

        <form className="form-stack" onSubmit={handleSubmit}>
          <label htmlFor="email">Correo electrónico</label>
          <input
            type="email"
            id="email"
            className="text-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label htmlFor="password">Contraseña</label>
          <input
            type="password"
            id="password"
            className="text-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />

          <div className="form-actions">
            <button type="submit" className="btn btn-primary">
              {isRegister ? "Crear cuenta" : "Entrar"}
            </button>
          </div>
        </form>

        <p className="help" style={{ marginTop: 16 }}>
          {isRegister ? "¿Ya tienes cuenta?" : "¿No tienes cuenta?"}{" "}
          <button
            className="btn btn-ghost btn-compact"
            onClick={() => setIsRegister(!isRegister)}
            style={{ padding: "4px 0", border: "none" }}
          >
            {isRegister ? "Inicia sesión" : "Regístrate"}
          </button>
        </p>
      </div>
    </div>
  );
}
