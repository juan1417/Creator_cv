import { emptyExperience, type Experience } from "../../../types/cv";
import { BulletList, DateInput, TextField, TextAreaField } from "./_form";

interface ExperienceSectionProps {
  value: Experience[];
  onChange: (next: Experience[]) => void;
}

export function ExperienceSection({ value, onChange }: ExperienceSectionProps) {
  const update = (i: number, patch: Partial<Experience>) => {
    const next = value.map((e, idx) => (idx === i ? { ...e, ...patch } : e));
    onChange(next);
  };
  const remove = (i: number) => onChange(value.filter((_, idx) => idx !== i));
  const add = () => onChange([...value, emptyExperience()]);

  return (
    <section className="editor-section">
      <div className="editor-section__head">
        <h3 className="editor-section__title">Experiencia</h3>
        <button type="button" className="btn btn-secondary btn-compact" onClick={add}>
          + Agregar
        </button>
      </div>

      {value.length === 0 ? (
        <p className="help">Sin entradas. Agregá tu primera experiencia.</p>
      ) : (
        <ul className="entry-list">
          {value.map((exp, i) => (
            <li key={i} className="entry-card">
              <div className="entry-card__head">
                <strong className="entry-card__title">
                  {exp.puesto || "(sin puesto)"}{" "}
                  {exp.empresa && (
                    <span className="entry-card__subtle">— {exp.empresa}</span>
                  )}
                </strong>
                <button
                  type="button"
                  className="btn btn-danger btn-compact"
                  onClick={() => remove(i)}
                  aria-label={`Eliminar experiencia ${i + 1}`}
                >
                  Eliminar
                </button>
              </div>

              <div className="form-stack" style={{ marginTop: 12 }}>
                <div className="form-row">
                  <TextField
                    label="Puesto"
                    htmlFor={`exp-${i}-puesto`}
                    value={exp.puesto}
                    onChange={(v) => update(i, { puesto: v })}
                    placeholder="Senior Developer"
                  />
                  <TextField
                    label="Empresa"
                    htmlFor={`exp-${i}-empresa`}
                    value={exp.empresa}
                    onChange={(v) => update(i, { empresa: v })}
                    placeholder="Acme Corp"
                  />
                </div>
                <div className="form-row">
                  <TextField
                    label="Ubicación"
                    htmlFor={`exp-${i}-ubicacion`}
                    value={exp.ubicacion}
                    onChange={(v) => update(i, { ubicacion: v })}
                    placeholder="Remoto / Buenos Aires"
                  />
                  <DateInput
                    label="Fecha inicio"
                    htmlFor={`exp-${i}-inicio`}
                    value={exp.fecha_inicio}
                    onChange={(v) => update(i, { fecha_inicio: v })}
                  />
                  <DateInput
                    label="Fecha fin (o vacío si seguís)"
                    htmlFor={`exp-${i}-fin`}
                    value={exp.fecha_fin}
                    onChange={(v) => update(i, { fecha_fin: v })}
                  />
                </div>

                <BulletList
                  label="Responsabilidades"
                  values={exp.responsabilidades}
                  onChange={(responsabilidades) => update(i, { responsabilidades })}
                  placeholder="Lideré la migración a microservicios…"
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
