import type { Skills } from "../../../types/cv";
import { TagInput } from "./_form";

interface SkillsSectionProps {
  value: Skills;
  onChange: (next: Skills) => void;
}

export function SkillsSection({ value, onChange }: SkillsSectionProps) {
  const update = <K extends keyof Skills>(key: K, v: Skills[K]) =>
    onChange({ ...value, [key]: v });

  return (
    <section className="editor-section">
      <h3 className="editor-section__title">Habilidades</h3>

      <div className="form-stack">
        <TagInput
          label="Técnicas"
          values={value.tecnicas}
          onChange={(tecnicas) => update("tecnicas", tecnicas)}
          placeholder="Python, SQL, AWS…"
        />
        <TagInput
          label="Habilidades blandas"
          values={value.blandas}
          onChange={(blandas) => update("blandas", blandas)}
          placeholder="Comunicación, liderazgo…"
        />
        <TagInput
          label="Idiomas"
          values={value.idiomas}
          onChange={(idiomas) => update("idiomas", idiomas)}
          placeholder="Español (nativo), Inglés (avanzado)…"
        />
        <TagInput
          label="Tecnologías / herramientas"
          values={value.tecnologias}
          onChange={(tecnologias) => update("tecnologias", tecnologias)}
          placeholder="React, Postgres, Docker, Git…"
        />
      </div>
    </section>
  );
}
