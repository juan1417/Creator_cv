import { useState } from "react";
import type { Skills } from "../../../types/cv";

interface SkillsSectionProps {
  value: Skills;
  onChange: (next: Skills) => void;
}

export function SkillsSection({ value, onChange }: SkillsSectionProps) {
  const [input, setInput] = useState("");

  const allSkills = [
    ...value.tecnicas,
    ...value.blandas,
    ...value.idiomas,
    ...value.tecnologias,
  ];

  const addSkill = (raw: string) => {
    const v = raw.trim();
    if (!v || allSkills.includes(v)) return;
    onChange({ ...value, tecnicas: [...value.tecnicas, v] });
  };

  const removeSkill = (v: string) => {
    const remove = (arr: string[]) => arr.filter((x) => x !== v);
    onChange({
      ...value,
      tecnicas: remove(value.tecnicas),
      blandas: remove(value.blandas),
      idiomas: remove(value.idiomas),
      tecnologias: remove(value.tecnologias),
    });
  };

  return (
    <div className="section-group">
      <div className="section-group-header">
        <div className="section-group-title">Habilidades</div>
        <button className="btn-ghost" type="button">✦ Mejorar con AI</button>
      </div>
      <div className="section-card">
        <div className="skills-wrap">
          {allSkills.map((skill) => (
            <span key={skill} className="skill-tag">
              {skill}
              <button className="skill-tag-remove" type="button" onClick={() => removeSkill(skill)} aria-label={`Eliminar ${skill}`}>✕</button>
            </span>
          ))}
          <input
            type="text"
            className="skill-add"
            placeholder="+ Agregar habilidad"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === ",") {
                e.preventDefault();
                addSkill(input);
                setInput("");
              }
            }}
            onBlur={() => { if (input.trim()) { addSkill(input); setInput(""); } }}
          />
        </div>
      </div>
    </div>
  );
}
