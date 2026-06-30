/** Templates de CV — fuente única de verdad para TemplatesPage, EditorPage y creación. */

import {
  emptyContext,
  emptyExperience,
  emptyEducation,
  type CVContext,
} from "../types/cv";

export type TemplateId =
  | "blank"
  | "minimal"
  | "professional"
  | "modern"
  | "executive"
  | "creative"
  | "academic";

export interface CVTemplate {
  id: TemplateId;
  name: string;
  description: string;
  tags: string[];
  context: CVContext;
}

function baseCtx(): CVContext {
  const ctx = emptyContext();
  ctx.meta.idioma_cv = "español";
  ctx.restricciones = {
    extension_maxima_paginas: 2,
    formato_solicitado: "PDF",
    otro: "",
  };
  return ctx;
}

function minimalCtx(): CVContext {
  return baseCtx();
}

function professionalCtx(): CVContext {
  const ctx = baseCtx();
  ctx.experiencia = [emptyExperience()];
  ctx.educacion = [emptyEducation()];
  return ctx;
}

function modernCtx(): CVContext {
  const ctx = baseCtx();
  ctx.experiencia = [emptyExperience()];
  ctx.educacion = [emptyEducation()];
  ctx.perfil_profesional.resumen = "";
  return ctx;
}

function executiveCtx(): CVContext {
  const ctx = baseCtx();
  ctx.experiencia = [emptyExperience(), emptyExperience()];
  ctx.educacion = [emptyEducation()];
  return ctx;
}

function creativeCtx(): CVContext {
  const ctx = baseCtx();
  ctx.experiencia = [emptyExperience()];
  ctx.educacion = [emptyEducation()];
  return ctx;
}

function academicCtx(): CVContext {
  const ctx = baseCtx();
  ctx.educacion = [emptyEducation()];
  ctx.certificaciones = [{ nombre: "", institucion: "", fecha: "" }];
  return ctx;
}

export const TEMPLATES: Record<TemplateId, CVTemplate> = {
  blank: {
    id: "blank",
    name: "En blanco",
    description: "Empezás desde cero. Ideal si querés control total.",
    tags: ["Personalizado"],
    context: emptyContext(),
  },
  minimal: {
    id: "minimal",
    name: "Minimal",
    description: "Limpio y profesional. Ideal para roles corporativos.",
    tags: ["Corporativo", "ATS-friendly"],
    context: minimalCtx(),
  },
  professional: {
    id: "professional",
    name: "Profesional",
    description: "CV tradicional con experiencia y educación pre-cargadas.",
    tags: ["Tradicional", "Formal"],
    context: professionalCtx(),
  },
  modern: {
    id: "modern",
    name: "Moderno",
    description: "Orientado a tecnología, con secciones de proyectos y skills.",
    tags: ["Tech", "Startups"],
    context: modernCtx(),
  },
  executive: {
    id: "executive",
    name: "Executive",
    description: "Formal y elegante para posiciones senior o directivas.",
    tags: ["Senior", "C-Suite"],
    context: executiveCtx(),
  },
  creative: {
    id: "creative",
    name: "Creative",
    description: "Para diseñadores y roles creativos. Más libertad visual.",
    tags: ["Diseño", "Portfolio"],
    context: creativeCtx(),
  },
  academic: {
    id: "academic",
    name: "Academic",
    description: "Para roles académicos, investigación y publicaciones.",
    tags: ["Investigación", "Universidad"],
    context: academicCtx(),
  },
};

export function getTemplate(id: TemplateId): CVTemplate {
  return TEMPLATES[id] ?? TEMPLATES.blank;
}
