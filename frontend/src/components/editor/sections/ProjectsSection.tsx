import { useState } from "react";
import { emptyProject, type Project } from "../../../types/cv";

interface ProjectsSectionProps {
  value: Project[];
  onChange: (next: Project[]) => void;
}

export function ProjectsSection({ value, onChange }: ProjectsSectionProps) {
  const [editing, setEditing] = useState<number | null>(null);

  const update = (i: number, patch: Partial<Project>) => {
    const next = value.map((p, idx) => (idx === i ? { ...p, ...patch } : p));
    onChange(next);
  };
  const remove = (i: number) => {
    onChange(value.filter((_, idx) => idx !== i));
    if (editing === i) setEditing(null);
  };
  const add = () => {
    onChange([...value, emptyProject()]);
    setEditing(value.length);
  };

  return (
    <div className="section-group">
      <div className="section-group-header">
        <div className="section-group-title">Proyectos</div>
        <button className="btn btn-s btn-sm" type="button" onClick={add}>+ Agregar</button>
      </div>
      <div className="section-card">
        {value.length === 0 ? (
          <p style={{ color: "var(--muted)", fontSize: 13 }}>Sin proyectos. Sumá side projects, OSS, etc.</p>
        ) : (
          value.map((proj, i) => (
            <div key={i} className="cv-item" onClick={() => setEditing(editing === i ? null : i)}>
              <div className="cv-item-header">
                <div>
                  <div className="cv-item-title">{proj.nombre || "(sin nombre)"}</div>
                  <div className="cv-item-subtitle">{[proj.rol, proj.tecnologias.join(", ")].filter(Boolean).join(" · ")}</div>
                  {proj.url && <div className="cv-item-date">{proj.url}</div>}
                </div>
                <div className="cv-item-actions">
                  <button className="cv-item-btn" title="Editar" type="button" onClick={(e) => { e.stopPropagation(); setEditing(editing === i ? null : i); }}>✎</button>
                  <button className="cv-item-btn" title="Eliminar" type="button" onClick={(e) => { e.stopPropagation(); remove(i); }}>✕</button>
                </div>
              </div>
              {proj.descripcion && (
                <div className="cv-item-desc">{proj.descripcion}</div>
              )}
              {editing === i && (
                <div className="form-row" style={{ marginTop: 12 }} onClick={(e) => e.stopPropagation()}>
                  <div className="form-group">
                    <label className="form-label">Nombre</label>
                    <input className="form-input" type="text" value={proj.nombre} onChange={(e) => update(i, { nombre: e.target.value })} placeholder="MiSaaS" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Rol</label>
                    <input className="form-input" type="text" value={proj.rol} onChange={(e) => update(i, { rol: e.target.value })} placeholder="Tech Lead" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">URL</label>
                    <input className="form-input" type="url" value={proj.url} onChange={(e) => update(i, { url: e.target.value })} placeholder="https://…" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tecnologías</label>
                    <input className="form-input" type="text" value={proj.tecnologias.join(", ")} onChange={(e) => update(i, { tecnologias: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} placeholder="Next.js, Prisma, Vercel…" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Descripción</label>
                    <textarea className="form-input form-textarea" rows={3} value={proj.descripcion} onChange={(e) => update(i, { descripcion: e.target.value })} />
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
