import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiListCVs, type CV } from "../lib/api";
import { useAuth } from "../lib/auth-context";
import { NewCVModal } from "../components/dashboard/NewCVModal";

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `hace ${mins} min`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `hace ${hrs}h`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `hace ${days} días`;
  const weeks = Math.floor(days / 7);
  return `hace ${weeks} semana${weeks > 1 ? "s" : ""}`;
}

export function HomePage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [cvs, setCVs] = useState<CV[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const load = async () => {
    try {
      const list = await apiListCVs();
      setCVs(list);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const name = auth.status === "authenticated" && auth.email ? auth.email.split("@")[0] : "Juan";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Buenos días" : hour < 18 ? "Buenas tardes" : "Buenas noches";

  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <div className="topbar-title">Dashboard</div>
        </div>
        <div className="topbar-actions">
          <button className="topbar-icon" aria-label="Favoritos">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </button>
        </div>
      </div>
      <div className="content">
      <div className="content-header">
        <h1>{greeting}, {name}</h1>
        <p>Tus CVs y actividad reciente</p>
      </div>

      {/* Stats — exactly as prototype */}
      <div className="stats">
        <div className="stat-card">
          <div className="stat-label">CVs creados</div>
          <div className="stat-value">{cvs.length}</div>
          <div className="stat-change stat-up">↑ 1 esta semana</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Puntaje promedio</div>
          <div className="stat-value">78</div>
          <div className="stat-change stat-up">↑ +5 vs anterior</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Comparaciones</div>
          <div className="stat-value">12</div>
          <div className="stat-change stat-up">↑ 4 este mes</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Mejoras aplicadas</div>
          <div className="stat-value">28</div>
          <div className="stat-change stat-up">↑ 6 nuevas</div>
        </div>
      </div>

      {/* CVs */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600 }}>Mis CVs</h2>
        <button className="btn btn-primary" onClick={() => setModalOpen(true)}>+ Nuevo CV</button>
      </div>

      {loading ? (
        <p className="empty-state">Cargando…</p>
      ) : (
        <div className="cv-grid">
          <div className="cv-card cv-card-new" onClick={() => setModalOpen(true)}>
            <div className="plus">+</div>
            <span style={{ fontSize: 13, fontWeight: 500 }}>Crear nuevo CV</span>
          </div>
          {cvs.map((cv) => (
            <div
              key={cv.id}
              className="cv-card"
              onClick={() => navigate(`/cv/${cv.id}`)}
            >
              <div className="cv-card-header">
                <div className="cv-card-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </div>
                <button className="cv-card-menu" onClick={(e) => e.stopPropagation()}>⋯</button>
              </div>
              <h3>{cv.title}</h3>
              <div className="cv-card-meta">
                {cv.context_json ? "2 páginas · React, TypeScript" : "1 página · Sin skills"}
              </div>
              <div className="cv-card-footer">
                <span className="cv-card-date">{timeAgo(cv.updated_at)}</span>
                <span className="cv-card-score">★ 85</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Activity + Progress — exactly as prototype */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div className="card-title">Actividad reciente</div>
          </div>
          <div className="card-body" style={{ padding: "12px 20px" }}>
            <div className="activity">
              <div className="activity-item">
                <div className="activity-dot" style={{ background: "var(--accent)" }} />
                <div>
                  <div className="activity-text">CV <strong>Frontend Developer</strong> mejorado con AI</div>
                  <div className="activity-time">Hace 2 horas</div>
                </div>
              </div>
              <div className="activity-item">
                <div className="activity-dot" style={{ background: "var(--color-success)" }} />
                <div>
                  <div className="activity-text">Comparación con oferta <strong>Senior Frontend</strong> — Puntaje: 85/100</div>
                  <div className="activity-time">Ayer</div>
                </div>
              </div>
              <div className="activity-item">
                <div className="activity-dot" style={{ background: "var(--color-warning)" }} />
                <div>
                  <div className="activity-text">CV <strong>Product Manager</strong> creado</div>
                  <div className="activity-time">Hace 3 días</div>
                </div>
              </div>
              <div className="activity-item">
                <div className="activity-dot" style={{ background: "var(--muted)" }} />
                <div>
                  <div className="activity-text">Sección <strong>Experiencia</strong> actualizada en CV Full Stack</div>
                  <div className="activity-time">Hace 1 semana</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <div className="card-title">Progreso del perfil</div>
          </div>
          <div className="card-body">
            <ProfileProgress label="Información personal" value={100} />
            <ProfileProgress label="Experiencia laboral" value={80} />
            <ProfileProgress label="Educación" value={60} />
            <ProfileProgress label="Habilidades" value={90} />
            <ProfileProgress label="Proyectos" value={30} />
          </div>
        </div>
      </div>

      <NewCVModal open={modalOpen} onClose={() => setModalOpen(false)} onCreated={load} />
      </div>
    </>
  );
}

function ProfileProgress({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 6 }}>
        <span>{label}</span>
        <span style={{ color: value >= 80 ? "var(--accent)" : "var(--muted)", fontWeight: 600 }}>{value}%</span>
      </div>
      <div className="progress">
        <div className="progress-bar" style={{ width: `${value}%`, background: value < 50 ? "var(--muted)" : undefined }} />
      </div>
    </div>
  );
}
