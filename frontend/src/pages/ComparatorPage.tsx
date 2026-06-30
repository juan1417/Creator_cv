import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiListCVs, apiCompareCV, type CV, type CompareResult } from "../lib/api";

const SUB_SCORE_LABELS: Record<string, string> = {
  experiencia: "Experiencia",
  habilidades: "Habilidades técnicas",
  educacion: "Formación",
  formato: "Formato / ATS",
};

const PRIORITY_LABELS: Record<string, string> = {
  alta: "Alto impacto",
  media: "Impacto medio",
  baja: "Bajo impacto",
};

export function ComparatorPage() {
  const navigate = useNavigate();
  const [cvs, setCvs] = useState<CV[]>([]);
  const [selectedCvId, setSelectedCvId] = useState("");
  const [offerTitle, setOfferTitle] = useState("");
  const [offerDesc, setOfferDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingCvs, setLoadingCvs] = useState(true);
  const [error, setError] = useState("");
  const [results, setResults] = useState<CompareResult | null>(null);

  useEffect(() => {
    apiListCVs()
      .then((data) => {
        setCvs(data);
        if (data.length > 0) setSelectedCvId(data[0].id);
      })
      .catch(() => {})
      .finally(() => setLoadingCvs(false));
  }, []);

  const runComparison = async () => {
    if (!selectedCvId || !offerTitle || !offerDesc) return;
    setLoading(true);
    setError("");
    try {
      const result = await apiCompareCV(selectedCvId, offerTitle, offerDesc);
      setResults(result);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const resetComparison = () => {
    setResults(null);
    setOfferTitle("");
    setOfferDesc("");
  };

  const selectedCv = cvs.find((c) => c.id === selectedCvId);

  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <div className="topbar-title">Comparador CV vs Oferta</div>
        </div>
      </div>
      <div className="content" style={{ maxWidth: 1100 }}>
        {!results ? (
          <>
            <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.01em", marginBottom: 4 }}>Compara tu CV con una oferta</h2>
            <p style={{ fontSize: 14, color: "var(--muted)", marginBottom: 24 }}>Selecciona tu CV y pega la descripción de la oferta laboral para obtener un análisis de compatibilidad con AI.</p>

            {error && <div className="flash flash-error" style={{ marginBottom: 16 }}>{error}</div>}

            <div className="input-section">
              <div className="card">
                <div className="card-header">
                  <div className="card-title">Tu CV</div>
                  {selectedCv && <span className="badge badge-blue">Seleccionado</span>}
                </div>
                <div className="card-body">
                  <div className="form-group">
                    <label className="form-label">Seleccionar CV</label>
                    <select
                      className="form-input"
                      value={selectedCvId}
                      onChange={(e) => setSelectedCvId(e.target.value)}
                      disabled={loadingCvs}
                    >
                      {loadingCvs ? (
                        <option>Cargando CVs…</option>
                      ) : cvs.length === 0 ? (
                        <option>No tenés CVs creados</option>
                      ) : (
                        cvs.map((cv) => (
                          <option key={cv.id} value={cv.id}>{cv.title}</option>
                        ))
                      )}
                    </select>
                  </div>
                  {selectedCv && (
                    <div style={{ background: "var(--bg)", borderRadius: "var(--radius)", padding: 14, fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>
                      <strong>{selectedCv.title}</strong> — Última edición: {new Date(selectedCv.updated_at).toLocaleDateString("es-AR")}
                    </div>
                  )}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <div className="card-title">Oferta laboral</div>
                </div>
                <div className="card-body">
                  <div className="form-group">
                    <label className="form-label">Nombre del puesto</label>
                    <input className="form-input" type="text" placeholder="ej. Senior Frontend Developer" value={offerTitle} onChange={(e) => setOfferTitle(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Descripción de la oferta</label>
                    <textarea className="form-input form-textarea" rows={8} placeholder="Pega aquí la descripción completa de la oferta laboral…" value={offerDesc} onChange={(e) => setOfferDesc(e.target.value)} />
                  </div>
                  <button
                    className="btn btn-primary btn-lg"
                    style={{ width: "100%" }}
                    onClick={runComparison}
                    disabled={loading || !selectedCvId || !offerTitle || !offerDesc}
                  >
                    {loading ? "Analizando con AI…" : "Analizar compatibilidad"}
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.01em", marginBottom: 4 }}>Resultado del análisis</h2>
                <p style={{ fontSize: 14, color: "var(--muted)" }}>CV vs {offerTitle}</p>
              </div>
              <button className="btn btn-secondary" onClick={resetComparison}>← Nuevo análisis</button>
            </div>

            <div className="score-grid">
              <div className="score-ring-wrap">
                <div className="score-ring">
                  <svg viewBox="0 0 180 180">
                    <circle className="score-ring-bg" cx="90" cy="90" r="80" />
                    <circle
                      className="score-ring-fill"
                      cx="90"
                      cy="90"
                      r="80"
                      stroke={results.score >= 80 ? "var(--color-success)" : results.score >= 60 ? "var(--color-warning)" : "var(--color-danger-fg)"}
                      strokeDasharray="502.6"
                      strokeDashoffset={502.6 - (results.score / 100) * 502.6}
                    />
                  </svg>
                  <div className="score-ring-center">
                    <div className="score-ring-value">{results.score}</div>
                    <div className="score-ring-label">de 100</div>
                  </div>
                </div>
                <div className="score-verdict" style={{ color: results.score >= 80 ? "var(--color-success)" : results.score >= 60 ? "var(--color-warning)" : "var(--color-danger-fg)" }}>
                  {results.verdict === "excelente" ? "¡Excelente compatibilidad!" : results.verdict === "bueno" ? "Buena compatibilidad" : results.verdict === "regular" ? "Compatibilidad regular" : "Necesita mejoras"}
                </div>
                <div className="score-subtext">
                  {results.score >= 80 ? "Tu CV se alinea muy bien con esta oferta." : results.score >= 60 ? "Cumples la mayoría de requisitos, pero hay áreas de mejora." : "Tu CV no cubre varios requisitos clave."}
                </div>
              </div>

              <div className="score-details">
                {Object.entries(results.sub_scores).map(([key, val]) => (
                  <div key={key} className="score-detail-card">
                    <div className="score-detail-header">
                      <div className="score-detail-name">{SUB_SCORE_LABELS[key] || key}</div>
                      <div className="score-detail-value">{val}/100</div>
                    </div>
                    <div className="score-detail-bar">
                      <div className="score-detail-fill" style={{ width: `${val}%`, background: val >= 70 ? "var(--color-success)" : val >= 50 ? "var(--color-warning)" : "var(--color-danger-fg)" }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Strengths */}
            {results.strengths.length > 0 && (
              <>
                <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, marginTop: 24 }}>Fortalezas</h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
                  {results.strengths.map((s, i) => (
                    <span key={i} style={{ background: "rgba(52, 199, 89, 0.1)", color: "var(--color-success)", padding: "6px 12px", borderRadius: 8, fontSize: 13 }}>{s}</span>
                  ))}
                </div>
              </>
            )}

            {/* Gaps */}
            {results.gaps.length > 0 && (
              <>
                <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>Áreas de mejora</h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
                  {results.gaps.map((g, i) => (
                    <span key={i} style={{ background: "rgba(255, 59, 48, 0.1)", color: "var(--color-danger-fg)", padding: "6px 12px", borderRadius: 8, fontSize: 13 }}>{g}</span>
                  ))}
                </div>
              </>
            )}

            {/* Improvements */}
            {results.improvements.length > 0 && (
              <>
                <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Mejoras sugeridas</h3>
                <div className="improvements-grid">
                  {results.improvements.map((imp, i) => (
                    <div key={i} className="improvement-card">
                      <div className="improvement-card-header">
                        <div className={`improvement-icon improvement-icon-${imp.priority === "alta" ? "high" : imp.priority === "media" ? "mid" : "low"}`}>✦</div>
                        <div>
                          <div className="improvement-title">{imp.title}</div>
                        </div>
                      </div>
                      <div className="improvement-text">{imp.description}</div>
                      <div className="improvement-impact">
                        <span className={`impact-badge impact-${imp.priority === "alta" ? "high" : imp.priority === "media" ? "mid" : "low"}`}>
                          {PRIORITY_LABELS[imp.priority] || imp.priority}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            <div className="improve-cta">
              <div className="improve-cta-text">
                <h3>¿Querés que el agente AI mejore tu CV?</h3>
                <p>El asistente puede reescribir secciones, agregar keywords faltantes y optimizar para ATS.</p>
              </div>
              <button className="btn btn-primary btn-lg" onClick={() => navigate(`/cv/${selectedCvId}`)}>Ir al Editor</button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
