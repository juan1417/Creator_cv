import { emptyEducation, type Education } from "../../../types/cv";
import { DateInput, TextField, TextAreaField } from "./_form";

interface EducationSectionProps {
  value: Education[];
  onChange: (next: Education[]) => void;
}

export function EducationSection({ value, onChange }: EducationSectionProps) {
  const update = (i: number, patch: Partial<Education>) => {
    const next = value.map((e, idx) => (idx === i ? { ...e, ...patch } : e));
    onChange(next);
  };
  const remove = (i: number) => onChange(value.filter((_, idx) => idx !== i));
  const add = () => onChange([...value, emptyEducation()]);

  return (
    <section className="editor-section">
      <div className="editor-section__head">
        <h3 className="editor-section__title">Educación</h3>
        <button type="button" className="btn btn-secondary btn-compact" onClick={add}>
          + Agregar
        </button>
      </div>

      {value.length === 0 ? (
        <p className="help">Sin entradas.</p>
      ) : (
        <ul className="entry-list">
          {value.map((edu, i) => (
            <li key={i} className="entry-card">
              <div className="entry-card__head">
                <strong className="entry-card__title">
                  {edu.titulo || "(sin título)"}
                </strong>
                <button
                  type="button"
                  className="btn btn-danger btn-compact"
                  onClick={() => remove(i)}
                  aria-label={`Eliminar educación ${i + 1}`}
                >
                  Eliminar
                </button>
              </div>

              <div className="form-stack" style={{ marginTop: 12 }}>
                <div className="form-row">
                  <TextField
                    label="Título"
                    htmlFor={`edu-${i}-titulo`}
                    value={edu.titulo}
                    onChange={(v) => update(i, { titulo: v })}
                    placeholder="Ingeniería en Sistemas"
                  />
                  <TextField
                    label="Institución"
                    htmlFor={`edu-${i}-institucion`}
                    value={edu.institucion}
                    onChange={(v) => update(i, { institucion: v })}
                    placeholder="UBA"
                  />
                  <DateInput
                    label="Año de graduación"
                    htmlFor={`edu-${i}-fin`}
                    value={edu.fecha_fin}
                    onChange={(v) => update(i, { fecha_fin: v })}
                  />
                </div>
                <TextAreaField
                  label="Descripción (opcional)"
                  htmlFor={`edu-${i}-desc`}
                  value={edu.descripcion}
                  onChange={(v) => update(i, { descripcion: v })}
                  placeholder="Tesis, mención, promedio…"
                  rows={2}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
