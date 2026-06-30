import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth-context";

const navPrincipal = [
  { to: "/", label: "Dashboard", icon: "dashboard" },
  { to: "/cvs", label: "Mis CVs", icon: "cvs" },
  { to: "/comparator", label: "Comparador", icon: "comparator" },
] as const;

const navTools = [
  { to: "/assistant", label: "Asistente AI", icon: "assistant" },
  { to: "/templates", label: "Plantillas", icon: "templates" },
  { to: "/history", label: "Historial", icon: "history" },
] as const;

function NavIcon({ name }: { name: string }) {
  switch (name) {
    case "dashboard":
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
      );
    case "cvs":
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      );
    case "comparator":
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <line x1="8" y1="6" x2="21" y2="6" />
          <line x1="8" y1="12" x2="21" y2="12" />
          <line x1="8" y1="18" x2="21" y2="18" />
          <line x1="3" y1="6" x2="3.01" y2="6" />
          <line x1="3" y1="12" x2="3.01" y2="12" />
          <line x1="3" y1="18" x2="3.01" y2="18" />
        </svg>
      );
    case "assistant":
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      );
    case "templates":
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <line x1="3" y1="9" x2="21" y2="9" />
          <line x1="9" y1="21" x2="9" y2="9" />
        </svg>
      );
    case "history":
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      );
    default:
      return null;
  }
}

function isActive(pathname: string, to: string) {
  if (to === "/") return pathname === "/";
  return pathname.startsWith(to);
}

export function Sidebar() {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  if (auth.status !== "authenticated") return null;

  const initials = auth.email
    ? auth.email.substring(0, 2).toUpperCase()
    : "U";

  return (
    <aside className="sidebar" role="navigation" aria-label="Navegación principal">
      <Link to="/" className="sidebar-brand">
        <span className="sidebar-brand-dot" aria-hidden="true" />
        CV Creator
      </Link>

      <div className="sidebar-section">Principal</div>
      {navPrincipal.map((item) => (
        <button
          key={item.to}
          className={`sidebar-link${isActive(location.pathname, item.to) ? " active" : ""}`}
          onClick={() => navigate(item.to)}
        >
          <span className="icon"><NavIcon name={item.icon} /></span>
          {item.label}
        </button>
      ))}

      <div className="sidebar-section">Herramientas</div>
      {navTools.map((item) => (
        <button
          key={item.to}
          className={`sidebar-link${isActive(location.pathname, item.to) ? " active" : ""}`}
          onClick={() => navigate(item.to)}
        >
          <span className="icon"><NavIcon name={item.icon} /></span>
          {item.label}
        </button>
      ))}

      <div className="sidebar-spacer" />

      <div className="sidebar-user">
        <div className="sidebar-avatar" aria-hidden="true">{initials}</div>
        <div className="sidebar-user-info">
          <div className="sidebar-user-name">{auth.email?.split("@")[0]}</div>
          <div className="sidebar-user-role">
            <Link to="/account" style={{ color: "inherit", textDecoration: "none" }}>
              Mi cuenta
            </Link>
          </div>
        </div>
      </div>
    </aside>
  );
}
