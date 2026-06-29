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
    <section className="editor-section">
      <h3 className="editor-section__title">Datos personales</h3>

      <div className="form-stack">
        <Field label="Nombre completo" htmlFor="meta-nombre">
          <input
            id="meta-nombre"
            type="text"
            className="text-input"
            value={value.nombre_completo}
            onChange={(e) => update("nombre_completo", e.target.value)}
            placeholder="Ada Lovelace"
          />
        </Field>

        <Field label="Título profesional" htmlFor="meta-titulo">
          <input
            id="meta-titulo"
            type="text"
            className="text-input"
            value={value.titulo_profesional}
            onChange={(e) => update("titulo_profesional", e.target.value)}
            placeholder="Senior Fullstack Developer"
          />
        </Field>

        <div className="form-row">
          <Field label="Email" htmlFor="meta-email">
            <input
              id="meta-email"
              type="email"
              className="text-input"
              value={value.contacto.email}
              onChange={(e) => updateContact("email", e.target.value)}
              placeholder="tu@email.com"
            />
          </Field>
          <Field label="Teléfono" htmlFor="meta-telefono">
            <input
              id="meta-telefono"
              type="tel"
              className="text-input"
              value={value.contacto.telefono}
              onChange={(e) => updateContact("telefono", e.target.value)}
              placeholder="+54 11 5555 5555"
            />
          </Field>
        </div>

        <Field label="LinkedIn" htmlFor="meta-linkedin">
          <input
            id="meta-linkedin"
            type="text"
            className="text-input"
            value={value.contacto.linkedin}
            onChange={(e) => updateContact("linkedin", e.target.value)}
            placeholder="linkedin.com/in/tu-usuario"
          />
        </Field>

        <Field label="Ubicación" htmlFor="meta-ubicacion">
          <input
            id="meta-ubicacion"
            type="text"
            className="text-input"
            value={value.contacto.ubicacion}
            onChange={(e) => updateContact("ubicacion", e.target.value)}
            placeholder="Buenos Aires, Argentina (o Remoto)"
          />
        </Field>

        <div className="form-row">
          <Field label="Tipo de CV" htmlFor="meta-tipo">
            <select
              id="meta-tipo"
              className="text-input"
              value={value.tipo_cv}
              onChange={(e) => update("tipo_cv", e.target.value)}
            >
              <option value="">—</option>
              <option value="tradicional">Tradicional</option>
              <option value="moderno">Moderno</option>
              <option value="academico">Académico</option>
              <option value="creativo">Creativo</option>
            </select>
          </Field>
          <Field label="Nivel de seniority" htmlFor="meta-seniority">
            <select
              id="meta-seniority"
              className="text-input"
              value={value.nivel_seniority}
              onChange={(e) => update("nivel_seniority", e.target.value)}
            >
              <option value="">—</option>
              <option value="junior">Junior</option>
              <option value="semi-senior">Semi-senior</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead / Staff</option>
            </select>
          </Field>
        </div>
      </div>
    </section>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="form-field">
      <label htmlFor={htmlFor} className="form-field__label">
        {label}
      </label>
      {children}
    </div>
  );
}
