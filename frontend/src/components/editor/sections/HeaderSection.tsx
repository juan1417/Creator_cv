import type { CVMeta } from "../../../types/cv";

interface HeaderSectionProps {
  value: CVMeta;
  onChange: (next: CVMeta) => void;
}

export function HeaderSection({ value, onChange }: HeaderSectionProps) {
  const update = <K extends keyof CVMeta>(key: K, v: CVMeta[K]) =>
    onChange({ ...value, [key]: v });

  const updateContact = <K extends keyof CVMeta["contacto"]>(
    key: K,
    v: CVMeta["contacto"][K]
  ) => onChange({ ...value, contacto: { ...value.contacto, [key]: v } });

  return (
    <div className="section-group">
      <div className="section-group-header">
        <div className="section-group-title">Información personal</div>
        <button className="btn-ghost" type="button">✦ Mejorar con AI</button>
      </div>
      <div className="section-card">
        <div className="form-row">
          <div className="form-group">
            <label className="form-label" htmlFor="cv-name">Nombre completo</label>
            <input className="form-input" type="text" id="cv-name"
              value={value.nombre_completo}
              onChange={(e) => update("nombre_completo", e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="cv-title">Título profesional</label>
            <input className="form-input" type="text" id="cv-title"
              value={value.titulo_profesional}
              onChange={(e) => update("titulo_profesional", e.target.value)}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label" htmlFor="cv-linkedin">LinkedIn</label>
            <input className="form-input" type="url" id="cv-linkedin"
              value={value.contacto.linkedin}
              onChange={(e) => updateContact("linkedin", e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="cv-portfolio">Portafolio</label>
            <input className="form-input" type="url" id="cv-portfolio" placeholder="https://tuproyecto.com"
              value={value.portafolio_url}
              onChange={(e) => update("portafolio_url", e.target.value)}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="cv-portfolio-desc">
            Descripción del portafolio <span style={{ color: "var(--muted)", fontWeight: 400, fontSize: 12 }}>(opcional)</span>
          </label>
          <input className="form-input" type="text" id="cv-portfolio-desc"
            placeholder="Proyectos personales, blog técnico, contribuciones open source..."
            value={value.portafolio_descripcion}
            onChange={(e) => update("portafolio_descripcion", e.target.value)}
          />
          <div className="form-hint">Describe brevemente qué encontrarán los reclutadores en tu portafolio.</div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label" htmlFor="cv-phone">Teléfono</label>
            <input className="form-input" type="tel" id="cv-phone"
              value={value.contacto.telefono}
              onChange={(e) => updateContact("telefono", e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="cv-location">Ubicación</label>
            <input className="form-input" type="text" id="cv-location"
              value={value.contacto.ubicacion}
              onChange={(e) => updateContact("ubicacion", e.target.value)}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="cv-summary">Resumen profesional</label>
          <textarea className="form-input form-textarea" id="cv-summary" rows={4}
            value={value.objetivo_cv}
            onChange={(e) => update("objetivo_cv", e.target.value)}
          />
          <div className="form-hint">Un buen resumen captura tu valor en 2-3 líneas. La AI puede ayudarte a mejorarlo.</div>
        </div>
      </div>
    </div>
  );
}
