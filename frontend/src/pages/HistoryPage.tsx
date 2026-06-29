import { useState } from "react";

type Tab = "all" | "edits" | "ai" | "versions";

const HISTORY_ITEMS = [
  { type: "ai", title: "Resumen profesional reescrito", cv: "CV Frontend Developer", time: "Hace 2 horas", details: "Mejorada la descripción del perfil con métricas específicas y keywords relevantes." },
  { type: "edit", title: "Experiencia laboral actualizada", cv: "CV Frontend Developer", time: "Hace 5 horas", details: "Agregada posición Senior Frontend en TechCorp con responsabilidades detalladas." },
  { type: "ai", title: "Skills optimizados para ATS", cv: "CV Frontend Developer", time: "Ayer", details: "Reordenamiento de habilidades técnicas por relevancia con la oferta." },
  { type: "version", title: "Versión 3 creada", cv: "CV Frontend Developer", time: "Hace 2 días", details: "Snapshot automático antes de cambios mayores." },
  { type: "edit", title: "Educación actualizada", cv: "CV Full Stack", time: "Hace 3 días", details: "Agregado curso de arquitectura de microservicios." },
  { type: "ai", title: "Descripción de proyecto mejorada", cv: "CV Full Stack", time: "Hace 4 días", details: "Reescrita la descripción del proyecto principal con impacto cuantificable." },
];

const CV_OPTIONS = [
  { id: "all", name: "Todos los CVs", count: HISTORY_ITEMS.length },
  { id: "frontend", name: "CV Frontend Developer", count: 4 },
  { id: "fullstack", name: "CV Full Stack", count: 2 },
];

export function HistoryPage() {
  const [tab, setTab] = useState<Tab>("all");
  const [selectedCV, setSelectedCV] = useState("all");

  const filtered = HISTORY_ITEMS.filter((item) => {
    if (selectedCV !== "all") {
      const cvName = selectedCV === "frontend" ? "CV Frontend Developer" : "CV Full Stack";
      if (item.cv !== cvName) return false;
    }
    if (tab === "all") return true;
    if (tab === "edits") return item.type === "edit";
    if (tab === "ai") return item.type === "ai";
    if (tab === "versions") return item.type === "version";
    return true;
  });

  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <div className="topbar-title">Historial</div>
        </div>
      </div>
      <div className="content">
      <div className="content-header">
        <h1>Historial de cambios</h1>
        <p>Revisa todas las ediciones, sugerencias AI y versiones de tus CVs.</p>
      </div>

      {/* CV Selector */}
      <div className="cv-selector">
        {CV_OPTIONS.map((cv) => (
          <button key={cv.id} className={`cv-option${selectedCV === cv.id ? " active" : ""}`} onClick={() => setSelectedCV(cv.id)}>
            <span className="cv-option-icon">📄</span>
            <div>
              <div className="cv-option-name">{cv.name}</div>
              <div className="cv-option-count">{cv.count} cambios</div>
            </div>
          </button>
        ))}
      </div>

      {/* Stats */}
      <div className="stats-bar">
        <div className="stat-card">
          <div className="stat-value">{filtered.length}</div>
          <div className="stat-label">Cambios totales</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{filtered.filter((i) => i.type === "ai").length}</div>
          <div className="stat-label">Mejoras AI</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{filtered.filter((i) => i.type === "version").length}</div>
          <div className="stat-label">Versiones</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{filtered.filter((i) => i.type === "edit").length}</div>
          <div className="stat-label">Ediciones manuales</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="history-tabs">
        {(["all", "edits", "ai", "versions"] as Tab[]).map((t) => (
          <button key={t} className={`history-tab${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>
            {t === "all" ? "Todos" : t === "edits" ? "Ediciones" : t === "ai" ? "AI" : "Versiones"}
          </button>
        ))}
      </div>

      {/* Timeline */}
      <div className="timeline">
        {filtered.map((item, i) => (
          <div key={i} className="timeline-item">
            <div className={`timeline-dot ${item.type === "ai" ? "timeline-dot-ai" : item.type === "edit" ? "timeline-dot-edit" : "timeline-dot-version"}`} />
            <div className="timeline-content">
              <div className="timeline-header">
                <div className="timeline-title">{item.title}</div>
                <div className="timeline-time">{item.time}</div>
              </div>
              <div className="timeline-cv">{item.cv}</div>
              <div className="timeline-details">{item.details}</div>
              <div className="timeline-actions">
                <span className={`badge ${item.type === "ai" ? "badge-blue" : item.type === "edit" ? "badge-green" : "badge-gray"}`}>
                  {item.type === "ai" ? "✦ AI" : item.type === "edit" ? "✎ Edición" : "⊞ Versión"}
                </span>
                <button className="btn btn-ghost" style={{ fontSize: 12 }}>Restaurar</button>
              </div>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="empty-state">
            <p>Sin cambios registrados</p>
          </div>
        )}
      </div>
      </div>
    </>
  );
}
