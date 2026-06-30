import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { apiGetHistory, apiRestoreHistory, type HistoryEntry } from "../lib/api";

type Tab = "all" | "created" | "edited" | "duplicated";

const TAB_LABELS: Record<Tab, string> = {
  all: "Todos",
  created: "Creaciones",
  edited: "Ediciones",
  duplicated: "Duplicados",
};

const EVENT_COLORS: Record<string, string> = {
  created: "badge-green",
  edited: "badge-blue",
  duplicated: "badge-gray",
};

const EVENT_LABELS: Record<string, string> = {
  created: "⊕ Creado",
  edited: "✎ Editado",
  duplicated: "⊞ Duplicado",
};

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "ahora mismo";
  if (mins < 60) return `hace ${mins} min`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `hace ${hrs}h`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return "ayer";
  return `hace ${days} dias`;
}

export function HistoryPage() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("all");
  const [selectedCV, setSelectedCV] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      setLoading(true);
      const data = await apiGetHistory();
      setEntries(data);
    } catch (err) {
      console.error("Failed to load history", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRestore(entryId: string, cvId: string) {
    if (!confirm("Restaurar este CV al estado de este punto?")) return;
    try {
      await apiRestoreHistory(entryId);
      navigate(`/editor/${cvId}`);
    } catch (err) {
      console.error("Failed to restore", err);
    }
  }

  const filtered = entries.filter((e) => {
    if (tab !== "all" && e.event_type !== tab) return false;
    if (selectedCV && e.cv_id !== selectedCV) return false;
    return true;
  });

  const cvIds = [...new Set(entries.map((e) => e.cv_id))];

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
          <p>Revisa todas las ediciones y creaciones de tus CVs.</p>
        </div>

        {/* CV Selector */}
        <div className="cv-selector">
          <button
            className={`cv-option${selectedCV === null ? " active" : ""}`}
            onClick={() => setSelectedCV(null)}
          >
            <span className="cv-option-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </span>
            <div>
              <div className="cv-option-name">Todos los CVs</div>
              <div className="cv-option-count">{entries.length} cambios</div>
            </div>
          </button>
          {cvIds.map((cvId) => {
            const count = entries.filter((e) => e.cv_id === cvId).length;
            return (
              <button
                key={cvId}
                className={`cv-option${selectedCV === cvId ? " active" : ""}`}
                onClick={() => setSelectedCV(cvId)}
              >
                <span className="cv-option-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </span>
                <div>
                  <div className="cv-option-name">CV {cvId.slice(0, 8)}</div>
                  <div className="cv-option-count">{count} cambios</div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Stats */}
        <div className="stats-bar">
          <div className="stat-card">
            <div className="stat-value">{filtered.length}</div>
            <div className="stat-label">Cambios totales</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{filtered.filter((i) => i.event_type === "created").length}</div>
            <div className="stat-label">Creaciones</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{filtered.filter((i) => i.event_type === "edited").length}</div>
            <div className="stat-label">Ediciones</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{filtered.filter((i) => i.event_type === "duplicated").length}</div>
            <div className="stat-label">Duplicados</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="history-tabs">
          {(Object.keys(TAB_LABELS) as Tab[]).map((t) => (
            <button key={t} className={`history-tab${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>
              {TAB_LABELS[t]}
            </button>
          ))}
        </div>

        {/* Timeline */}
        {loading ? (
          <div className="empty-state">
            <p>Cargando historial...</p>
          </div>
        ) : (
          <div className="timeline">
            {filtered.map((item) => (
              <div key={item.id} className="timeline-item">
                <div className={`timeline-dot ${item.event_type === "edited" ? "timeline-dot-edit" : item.event_type === "created" ? "timeline-dot-version" : "timeline-dot-ai"}`} />
                <div className="timeline-content">
                  <div className="timeline-header">
                    <div className="timeline-title">{item.title}</div>
                    <div className="timeline-time">{timeAgo(item.created_at)}</div>
                  </div>
                  <div className="timeline-cv">CV {item.cv_id.slice(0, 8)}</div>
                  <div className="timeline-details">{item.description}</div>
                  <div className="timeline-actions">
                    <span className={`badge ${EVENT_COLORS[item.event_type] || "badge-gray"}`}>
                      {EVENT_LABELS[item.event_type] || item.event_type}
                    </span>
                    <button
                      className="btn btn-ghost"
                      style={{ fontSize: 12 }}
                      onClick={() => handleRestore(item.id, item.cv_id)}
                    >
                      Restaurar
                    </button>
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
        )}
      </div>
    </>
  );
}
