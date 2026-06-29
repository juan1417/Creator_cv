import type { CVProfile } from "../../../types/cv";
import { TagInput } from "./_form";

interface ProfileSectionProps {
  value: CVProfile;
  onChange: (next: CVProfile) => void;
}

export function ProfileSection({ value, onChange }: ProfileSectionProps) {
  return (
    <section className="editor-section">
      <h3 className="editor-section__title">Perfil profesional</h3>

      <div className="form-stack">
        <div className="form-field">
          <label htmlFor="perfil-resumen" className="form-field__label">
            Resumen
          </label>
          <textarea
            id="perfil-resumen"
            className="text-input"
            rows={4}
            value={value.resumen}
            onChange={(e) => onChange({ ...value, resumen: e.target.value })}
            placeholder="Desarrollador fullstack con 8 años de experiencia…"
          />
        </div>

        <TagInput
          label="Palabras clave"
          values={value.palabras_clave}
          onChange={(palabras_clave) => onChange({ ...value, palabras_clave })}
          placeholder="TypeScript, React, Postgres…"
        />
      </div>
    </section>
  );
}


