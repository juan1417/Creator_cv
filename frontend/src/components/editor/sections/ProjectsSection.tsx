import { emptyProject, type Project } from "../../../types/cv";
import { TagInput, TextField, TextAreaField } from "./_form";

interface ProjectsSectionProps {
  value: Project[];
  onChange: (next: Project[]) => void;
}

export function ProjectsSection({ value, onChange }: ProjectsSectionProps) {
  const update = (i: number, patch: Partial<Project>) => {
    const next = value.map((p, idx) => (idx === i ? { ...p, ...patch } : p));
    onChange(next);
  };
  const remove = (i: number) => onChange(value.filter((_, idx) => idx !== i));
  const add = () => onChange([...value, emptyProject()]);

  return (
    <section className="editor-section">
      <div className="editor-section__head">
        <h3 className="editor-section__title">Proyectos</h3>
        <button type="button" className="btn btn-secondary btn-compact" onClick={add}>
          + Agregar
        </button>
      </div>

      {value.length === 0 ? (
        <p className="help">Sin proyectos. Sumá side projects, OSS, etc.</p>
      ) : (
        <ul className="entry-list">
          {value.map((proj, i) => (
            <li key={i} className="entry-card">
              <div className="entry-card__head">
                <strong className="entry-card__title">
                  {proj.nombre || "(sin nombre)"}
                </strong>
                <button
                  type="button"
                  className="btn btn-danger btn-compact"
                  onClick={() => remove(i)}
                  aria-label={`Eliminar proyecto ${i + 1}`}
                >
                  Eliminar
                </button>
              </div>

              <div className="form-stack" style={{ marginTop: 12 }}>
                <div className="form-row">
                  <TextField
                    label="Nombre"
                    htmlFor={`proj-${i}-nombre`}
                    value={proj.nombre}
                    onChange={(v) => update(i, { nombre: v })}
                    placeholder="MiSaaS"
                  />
                  <TextField
                    label="Rol"
                    htmlFor={`proj-${i}-rol`}
                    value={proj.rol}
                    onChange={(v) => update(i, { rol: v })}
                    placeholder="Tech Lead"
                  />
                  <TextField
                    label="URL"
                    htmlFor={`proj-${i}-url`}
                    value={proj.url}
                    onChange={(v) => update(i, { url: v })}
                    placeholder="https://…"
                  />
                </div>
                <TagInput
                  label="Tecnologías"
                  values={proj.tecnologias}
                  onChange={(tecnologias) => update(i, { tecnologias })}
                  placeholder="Next.js, Prisma, Vercel…"
                />
                <TextAreaField
                  label="Descripción"
                  htmlFor={`proj-${i}-desc`}
                  value={proj.descripcion}
                  onChange={(v) => update(i, { descripcion: v })}
                  rows={3}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
