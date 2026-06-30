import { useState } from "react";
import { emptyExperience, type Experience } from "../../../types/cv";

interface ExperienceSectionProps {
  value: Experience[];
  onChange: (next: Experience[]) => void;
}

export function ExperienceSection({ value, onChange }: ExperienceSectionProps) {
  const [editing, setEditing] = useState<number | null>(null);

  const update = (i: number, patch: Partial<Experience>) => {
    const next = value.map((e, idx) => (idx === i ? { ...e, ...patch } : e));
    onChange(next);
  };
  const remove = (i: number) => {
    onChange(value.filter((_, idx) => idx !== i));
    if (editing === i) setEditing(null);
  };
  const add = () => {
    onChange([...value, emptyExperience()]);
    setEditing(value.length);
  };

  return (
    <div className="section-group">
      <div className="section-group-header">
        <div className="section-group-title">Experiencia laboral</div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn-ghost" type="button">✦ Mejorar con AI</button>
          <button className="btn btn-s btn-sm" type="button" onClick={add}>+ Agregar</button>
        </div>
      </div>
      <div className="section-card">
        {value.length === 0 ? (
          <p style={{ color: "var(--muted)", fontSize: 13 }}>Sin entradas. Agregá tu primera experiencia.</p>
        ) : (
          value.map((exp, i) => (
            <div key={i} className="cv-item" onClick={() => setEditing(editing === i ? null : i)}>
              <div className="cv-item-header">
                <div>
                  <div className="cv-item-title">{exp.puesto || "(sin puesto)"}</div>
                  <div className="cv-item-subtitle">
                    {[exp.empresa, exp.ubicacion].filter(Boolean).join(" · ")}
                  </div>
                  <div className="cv-item-date">
                    {[exp.fecha_inicio, exp.fecha_fin || "Actualidad"].filter(Boolean).join(" – ")}
                  </div>
                </div>
                <div className="cv-item-actions">
                  <button className="cv-item-btn" title="Editar" type="button" onClick={(e) => { e.stopPropagation(); setEditing(editing === i ? null : i); }}>✎</button>
                  <button className="cv-item-btn" title="Eliminar" type="button" onClick={(e) => { e.stopPropagation(); remove(i); }}>✕</button>
                </div>
              </div>
              {exp.responsabilidades.length > 0 && (
                <div className="cv-item-desc">
                  {exp.responsabilidades.filter(Boolean).join(". ")}
                </div>
              )}
              {editing === i && (
                <div className="form-row" style={{ marginTop: 12 }} onClick={(e) => e.stopPropagation()}>
                  <div className="form-group">
                    <label className="form-label">Puesto</label>
                    <input className="form-input" type="text" value={exp.puesto} onChange={(e) => update(i, { puesto: e.target.value })} placeholder="Senior Developer" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Empresa</label>
                    <input className="form-input" type="text" value={exp.empresa} onChange={(e) => update(i, { empresa: e.target.value })} placeholder="Acme Corp" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Ubicación</label>
                    <input className="form-input" type="text" value={exp.ubicacion} onChange={(e) => update(i, { ubicacion: e.target.value })} placeholder="Remoto / Buenos Aires" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Fecha inicio</label>
                    <input className="form-input" type="month" value={exp.fecha_inicio} onChange={(e) => update(i, { fecha_inicio: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Fecha fin</label>
                    <input className="form-input" type="month" value={exp.fecha_fin} onChange={(e) => update(i, { fecha_fin: e.target.value })} />
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
