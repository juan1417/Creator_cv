/** Templates de CV para el wizard de "Nuevo CV". Solo constantes — sin backend. */

import {
  emptyContext,
  emptyExperience,
  emptyEducation,
  type CVContext,
} from "../types/cv";

export type TemplateId = "blank" | "classic" | "modern";

export interface CVTemplate {
  id: TemplateId;
  name: string;
  description: string;
  context: CVContext;
}

function classicContext(): CVContext {
  const ctx = emptyContext();
  ctx.meta.idioma_cv = "español";
  ctx.meta.tipo_cv = "tradicional";
  ctx.meta.nivel_seniority = "semi-senior";
  ctx.restricciones = {
    extension_maxima_paginas: 2,
    formato_solicitado: "PDF",
    otro: "",
  };
  return ctx;
}

function modernContext(): CVContext {
  const ctx = emptyContext();
  ctx.meta.idioma_cv = "español";
  ctx.meta.tipo_cv = "moderno";
  ctx.meta.nivel_seniority = "senior";
  ctx.restricciones = {
    extension_maxima_paginas: 2,
    formato_solicitado: "PDF",
    otro: "",
  };
  // Placeholders de muestra — el usuario los completa
  ctx.experiencia = [emptyExperience()];
  ctx.educacion = [emptyEducation()];
  return ctx;
}

export const TEMPLATES: Record<TemplateId, CVTemplate> = {
  blank: {
    id: "blank",
    name: "En blanco",
    description: "Empezás desde cero. Ideal si querés control total.",
    context: emptyContext(),
  },
  classic: {
    id: "classic",
    name: "Clásico",
    description: "CV tradicional en español, 2 páginas. Para roles formales.",
    context: classicContext(),
  },
  modern: {
    id: "modern",
    name: "Moderno",
    description: "Orientado a tecnología, con secciones de proyectos y skills.",
    context: modernContext(),
  },
};

export function getTemplate(id: TemplateId): CVTemplate {
  return TEMPLATES[id] ?? TEMPLATES.blank;
}
