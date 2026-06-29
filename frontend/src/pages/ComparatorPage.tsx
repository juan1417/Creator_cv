import { useState } from "react";

const SCORE_DETAILS = [
  { name: "Habilidades técnicas", key: "skills" },
  { name: "Experiencia", key: "exp" },
  { name: "Formación", key: "edu" },
  { name: "Keywords / ATS", key: "ats" },
] as const;

const IMPROVEMENTS = [
  { title: "Agregar keywords de la oferta", category: "ATS Optimization", text: "Tu CV no incluye varias palabras clave requeridas. Agregarlas aumenta la compatibilidad ATS significativamente.", impact: "high" as const, icon: "🎯" },
  { title: "Incrementar experiencia", category: "Experiencia", text: "Puedes reencuadrar experiencia freelance o proyectos personales para alcanzar el mínimo requerido.", impact: "mid" as const, icon: "📊" },
  { title: "Agregar sección de testing", category: "Habilidades técnicas", text: "No mencionas experiencia con testing frameworks. Incluye al menos un proyecto donde los hayas usado.", impact: "high" as const, icon: "🧪" },
  { title: "Mencionar liderazgo técnico", category: "Soft Skills", text: "La oferta busca capacidad de liderazgo. Agrega: tamaño del equipo, metodología, resultados.", impact: "mid" as const, icon: "👥" },
  { title: "Incluir nivel de inglés", category: "Idiomas", text: "La oferta requiere nivel de inglés. Agrega un nivel CEFR (ej. B2, C1) o resultado de certificación.", impact: "low" as const, icon: "🌐" },
  { title: "Destacar contribuciones open source", category: "Diferenciador", text: "Si tienes repos activos o PRs contribuidos, destácalo prominentemente.", impact: "low" as const, icon: "⭐" },
];

export function ComparatorPage() {
  const [showResults, setShowResults] = useState(false);
  const [offerTitle, setOfferTitle] = useState("");
  const [offerDesc, setOfferDesc] = useState("");

  const runComparison = () => {
    if (!offerTitle || !offerDesc) return;
    setShowResults(true);
  };

  const resetComparison = () => {
    setShowResults(false);
    setOfferTitle("");
    setOfferDesc("");
  };

  const score = 72;

  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <div className="topbar-title">Comparador CV vs Oferta</div>
        </div>
      </div>
      <div className="content" style={{ maxWidth: 1100 }}>
      {!showResults ? (
        <>
          <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.01em", marginBottom: 4 }}>Compara tu CV con una oferta</h2>
          <p style={{ fontSize: 14, color: "var(--muted)", marginBottom: 24 }}>Selecciona tu CV y pega la descripción de la oferta laboral para obtener un análisis de compatibilidad.</p>

          <div className="input-section">
            <div className="card">
              <div className="card-header">
                <div className="card-title">Tu CV</div>
                <span className="badge badge-blue">Seleccionado</span>
              </div>
              <div className="card-body">
                <div className="form-group">
                  <label className="form-label">Seleccionar CV</label>
                  <select className="form-input">
                    <option>Seleccioná un CV…</option>
                  </select>
                </div>
                <div style={{ background: "var(--bg)", borderRadius: "var(--radius)", padding: 14, fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>
                  Seleccioná un CV para ver su resumen aquí.
                </div>
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
                <button className="btn btn-primary btn-lg" style={{ width: "100%" }} onClick={runComparison}>Analizar compatibilidad</button>
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
                  <circle className="score-ring-fill" cx="90" cy="90" r="80" stroke={score >= 80 ? "var(--color-success)" : score >= 60 ? "var(--color-warning)" : "var(--color-danger-fg)"} strokeDasharray="502.6" strokeDashoffset={502.6 - (score / 100) * 502.6} />
                </svg>
                <div className="score-ring-center">
                  <div className="score-ring-value">{score}</div>
                  <div className="score-ring-label">de 100</div>
                </div>
              </div>
              <div className="score-verdict" style={{ color: score >= 80 ? "var(--color-success)" : score >= 60 ? "var(--color-warning)" : "var(--color-danger-fg)" }}>
                {score >= 80 ? "¡Excelente compatibilidad!" : score >= 60 ? "Buena compatibilidad" : "Necesita mejoras"}
              </div>
              <div className="score-subtext">
                {score >= 80 ? "Tu CV se alinea muy bien con esta oferta." : score >= 60 ? "Cumples la mayoría de requisitos, pero hay áreas de mejora." : "Tu CV no cubre varios requisitos clave."}
              </div>
            </div>

            <div className="score-details">
              {SCORE_DETAILS.map((d) => (
                <div key={d.key} className="score-detail-card">
                  <div className="score-detail-header">
                    <div className="score-detail-name">{d.name}</div>
                    <div className="score-detail-value">{Math.floor(Math.random() * 40 + 50)}/100</div>
                  </div>
                  <div className="score-detail-bar"><div className="score-detail-fill" style={{ width: `${Math.floor(Math.random() * 40 + 50)}%`, background: "var(--accent)" }} /></div>
                </div>
              ))}
            </div>
          </div>

          <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Puntos que fallan — Mejoras sugeridas</h3>
          <div className="improvements-grid">
            {IMPROVEMENTS.map((imp, i) => (
              <div key={i} className="improvement-card">
                <div className="improvement-card-header">
                  <div className={`improvement-icon improvement-icon-${imp.impact}`}>{imp.icon}</div>
                  <div>
                    <div className="improvement-title">{imp.title}</div>
                    <div className="improvement-category">{imp.category}</div>
                  </div>
                </div>
                <div className="improvement-text">{imp.text}</div>
                <div className="improvement-impact">
                  <span className={`impact-badge impact-${imp.impact}`}>
                    {imp.impact === "high" ? "Alto impacto" : imp.impact === "mid" ? "Impacto medio" : "Bajo impacto"}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="improve-cta">
            <div className="improve-cta-text">
              <h3>¿Querés que el agente AI mejore tu CV?</h3>
              <p>El asistente puede reescribir secciones, agregar keywords faltantes y optimizar para ATS.</p>
            </div>
            <button className="btn btn-primary btn-lg">✦ Mejorar CV con AI</button>
          </div>
        </>
      )}
      </div>
    </>
  );
}
