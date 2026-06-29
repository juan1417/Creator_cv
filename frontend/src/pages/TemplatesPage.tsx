const TEMPLATES = [
  { id: "minimal", name: "Minimal", desc: "Limpio y profesional. Ideal para roles corporativos.", color: "var(--fg)", tags: ["Corporativo", "ATS-friendly"] },
  { id: "modern", name: "Modern", desc: "Diseño contemporáneo con acentos de color.", color: "var(--accent)", tags: ["Tech", "Startups"] },
  { id: "creative", name: "Creative", desc: "Para diseñadores y roles creativos.", color: "#5856d6", tags: ["Diseño", "Portfolio"] },
  { id: "executive", name: "Executive", desc: "Formal y elegante para posiciones senior.", color: "var(--fg)", tags: ["Senior", "C-Suite"] },
  { id: "academic", name: "Academic", desc: "Para roles académicos e investigación.", color: "var(--fg)", tags: ["Investigación", "Universidad"] },
  { id: "tech", name: "Tech", desc: "Optimizado para roles de ingeniería.", color: "var(--accent)", tags: ["Engineering", "DevOps"] },
];

export function TemplatesPage() {
  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <div className="topbar-title">Plantillas</div>
        </div>
      </div>
      <div className="content">
      <div className="content-header" style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1>Plantillas</h1>
          <p>Elegí una plantilla para empezar tu CV.</p>
        </div>
        <button className="btn btn-primary">+ Crear plantilla</button>
      </div>

      <div className="template-grid">
        {TEMPLATES.map((tpl) => (
          <div key={tpl.id} className="template-card" style={{ borderTopColor: tpl.color }}>
            <div className="template-preview">
              <div className="template-mini">
                <div className="tp-name-bar" style={{ background: tpl.color }} />
                <div className="tp-role-bar" />
                <div className="tp-section-title" style={{ background: tpl.color }} />
                <div className="tp-line" /><div className="tp-line" /><div className="tp-line" style={{ width: "60%" }} />
                <div className="tp-section-title" style={{ background: tpl.color }} />
                <div className="tp-line" /><div className="tp-line" style={{ width: "80%" }} />
              </div>
            </div>
            <div className="template-info">
              <h3 className="template-name">{tpl.name}</h3>
              <p className="template-desc">{tpl.desc}</p>
              <div className="template-tags">
                {tpl.tags.map((t) => <span key={t} className="template-tag">{t}</span>)}
              </div>
              <div className="template-actions">
                <button className="btn btn-primary" style={{ flex: 1 }}>Usar plantilla</button>
                <button className="btn btn-secondary">Vista previa</button>
              </div>
            </div>
          </div>
        ))}
      </div>
      </div>
    </>
  );
}
