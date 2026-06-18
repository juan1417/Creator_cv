import { useAuth } from "../lib/auth-context";

export function SiteHeader() {
  const auth = useAuth();
  if (auth.status !== "authenticated") return null;

  return (
    <header className="site-header">
      <nav className="wrap" aria-label="Navegación principal">
        <a href="/" className="brand">
          Creator CV
        </a>
        <div className="site-header__user">
          <span className="site-header__email">{auth.email}</span>
          <button
            className="btn btn-ghost btn-compact"
            onClick={() => auth.signOut()}
          >
            Cerrar sesión
          </button>
        </div>
      </nav>
    </header>
  );
}
