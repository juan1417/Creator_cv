import { useState } from "react";
import { emptyEducation, type Education } from "../../../types/cv";

interface EducationSectionProps {
  value: Education[];
  onChange: (next: Education[]) => void;
}

export function EducationSection({ value, onChange }: EducationSectionProps) {
  const [editing, setEditing] = useState<number | null>(null);

  const update = (i: number, patch: Partial<Education>) => {
    const next = value.map((e, idx) => (idx === i ? { ...e, ...patch } : e));
    onChange(next);
  };
  const remove = (i: number) => {
    onChange(value.filter((_, idx) => idx !== i));
    if (editing === i) setEditing(null);
  };
  const add = () => {
    onChange([...value, emptyEducation()]);
    setEditing(value.length);
  };

  return (
    <div className="section-group">
      <div className="section-group-header">
        <div className="section-group-title">Educación</div>
        <button className="btn btn-s btn-sm" type="button" onClick={add}>+ Agregar</button>
      </div>
      <div className="section-card">
        {value.length === 0 ? (
          <p style={{ color: "var(--muted)", fontSize: 13 }}>Sin entradas.</p>
        ) : (
          value.map((edu, i) => (
            <div key={i} className="cv-item" onClick={() => setEditing(editing === i ? null : i)}>
              <div className="cv-item-header">
                <div>
                  <div className="cv-item-title">{edu.titulo || "(sin título)"}</div>
                  <div className="cv-item-subtitle">{edu.institucion}</div>
                  <div className="cv-item-date">{edu.fecha_fin}</div>
                </div>
                <div className="cv-item-actions">
                  <button className="cv-item-btn" title="Editar" type="button" onClick={(e) => { e.stopPropagation(); setEditing(editing === i ? null : i); }}>✎</button>
                  <button className="cv-item-btn" title="Eliminar" type="button" onClick={(e) => { e.stopPropagation(); remove(i); }}>✕</button>
                </div>
              </div>
              {editing === i && (
                <div className="form-row" style={{ marginTop: 12 }} onClick={(e) => e.stopPropagation()}>
                  <div className="form-group">
                    <label className="form-label">Título</label>
                    <input className="form-input" type="text" value={edu.titulo} onChange={(e) => update(i, { titulo: e.target.value })} placeholder="Ingeniería en Sistemas" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Institución</label>
                    <input className="form-input" type="text" value={edu.institucion} onChange={(e) => update(i, { institucion: e.target.value })} placeholder="UBA" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Año de graduación</label>
                    <input className="form-input" type="month" value={edu.fecha_fin} onChange={(e) => update(i, { fecha_fin: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Descripción (opcional)</label>
                    <textarea className="form-input form-textarea" rows={2} value={edu.descripcion} onChange={(e) => update(i, { descripcion: e.target.value })} placeholder="Tesis, mención, promedio…" />
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
