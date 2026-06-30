/** Schema tipado del contexto JSON del CV. */

export interface CVMeta {
  nombre_completo: string;
  titulo_profesional: string;
  idioma_cv: string;
  objetivo_cv: string;
  portafolio_url: string;
  portafolio_descripcion: string;
  contacto: {
    telefono: string;
    email: string;
    linkedin: string;
    ubicacion: string;
  };
}

export interface CVProfile {
  resumen: string;
  palabras_clave: string[];
}

export interface Experience {
  puesto: string;
  empresa: string;
  ubicacion: string;
  fecha_inicio: string;
  fecha_fin: string;
  responsabilidades: string[];
}

export interface Education {
  titulo: string;
  institucion: string;
  fecha_fin: string;
  descripcion: string;
}

export interface Skills {
  tecnicas: string[];
  blandas: string[];
  idiomas: string[];
  tecnologias: string[];
}

export interface Project {
  nombre: string;
  rol: string;
  tecnologias: string[];
  url: string;
  descripcion: string;
}

export interface Certification {
  nombre: string;
  institucion: string;
  fecha: string;
}

export interface Fortaleza {
  nombre: string;
  descripcion: string;
}

export interface Recurso {
  cv_existente: boolean;
  texto_cv: string;
  links: string[];
}

export interface Restricciones {
  extension_maxima_paginas: number;
  formato_solicitado: string;
  otro: string;
}

export interface CVContext {
  meta: CVMeta;
  certificaciones: Certification[];
  fortalezas: Fortaleza[];
  perfil_profesional: CVProfile;
  experiencia: Experience[];
  educacion: Education[];
  habilidades: Skills;
  proyectos: Project[];
  recursos_actuales: Recurso;
  restricciones: Restricciones;
  dudas_pendientes: string[];
}

// ── Defaults (factory functions — no mutar objetos compartidos) ─────────

export function emptyContact() {
  return { telefono: "", email: "", linkedin: "", ubicacion: "" };
}

export function emptyMeta(): CVMeta {
  return {
    nombre_completo: "",
    titulo_profesional: "",
    idioma_cv: "español",
    objetivo_cv: "",
    portafolio_url: "",
    portafolio_descripcion: "",
    contacto: emptyContact(),
  };
}

export function emptyProfile(): CVProfile {
  return { resumen: "", palabras_clave: [] };
}

export function emptyExperience(): Experience {
  return {
    puesto: "",
    empresa: "",
    ubicacion: "",
    fecha_inicio: "",
    fecha_fin: "",
    responsabilidades: [],
  };
}

export function emptyEducation(): Education {
  return {
    titulo: "",
    institucion: "",
    fecha_fin: "",
    descripcion: "",
  };
}

export function emptySkills(): Skills {
  return { tecnicas: [], blandas: [], idiomas: [], tecnologias: [] };
}

export function emptyProject(): Project {
  return {
    nombre: "",
    rol: "",
    tecnologias: [],
    url: "",
    descripcion: "",
  };
}

export function emptyCertification(): Certification {
  return { nombre: "", institucion: "", fecha: "" };
}

export function emptyFortaleza(): Fortaleza {
  return { nombre: "", descripcion: "" };
}

export function emptyRecurso(): Recurso {
  return { cv_existente: false, texto_cv: "", links: [] };
}

export function emptyRestricciones(): Restricciones {
  return {
    extension_maxima_paginas: 1,
    formato_solicitado: "PDF",
    otro: "",
  };
}

export function emptyContext(): CVContext {
  return {
    meta: emptyMeta(),
    certificaciones: [],
    fortalezas: [],
    perfil_profesional: emptyProfile(),
    experiencia: [],
    educacion: [],
    habilidades: emptySkills(),
    proyectos: [],
    recursos_actuales: emptyRecurso(),
    restricciones: emptyRestricciones(),
    dudas_pendientes: [],
  };
}

// ── Helpers ──────────────────────────────────────────────────────────────

/**
 * Parsea ``context_json`` del backend tolerando campos faltantes.
 *
 * Antes este parseo vivía en ``CVRenderer`` con un montón de ``asString`` /
 * ``asArray`` defensivos. Ahora con tipos tipados podemos dar defaults explícitos.
 */
export function parseContext(raw: string): CVContext {
  let parsed: unknown = {};
  try {
    parsed = JSON.parse(raw);
  } catch {
    return emptyContext();
  }
  if (!parsed || typeof parsed !== "object") return emptyContext();
  const obj = parsed as Record<string, unknown>;

  const m = (obj.meta as Record<string, unknown> | undefined) ?? {};
  const contacto = (m.contacto as Record<string, unknown> | undefined) ?? {};
  const meta: CVMeta = {
    nombre_completo: str(m.nombre_completo),
    titulo_profesional: str(m.titulo_profesional),
    idioma_cv: str(m.idioma_cv) || "español",
    objetivo_cv: str(m.objetivo_cv),
    portafolio_url: str(m.portafolio_url),
    portafolio_descripcion: str(m.portafolio_descripcion),
    contacto: {
      telefono: str(contacto.telefono),
      email: str(contacto.email),
      linkedin: str(contacto.linkedin),
      ubicacion: str(contacto.ubicacion),
    },
  };

  const p = (obj.perfil_profesional as Record<string, unknown> | undefined) ?? {};
  const perfil_profesional: CVProfile = {
    resumen: str(p.resumen),
    palabras_clave: arr(p.palabras_clave),
  };

  const experiencia: Experience[] = (arr(obj.experiencia) as unknown[]).map(
    (e) => {
      const x = (e ?? {}) as Record<string, unknown>;
      return {
        puesto: str(x.puesto),
        empresa: str(x.empresa),
        ubicacion: str(x.ubicacion),
        fecha_inicio: str(x.fecha_inicio),
        fecha_fin: str(x.fecha_fin),
        responsabilidades: arr(x.responsabilidades),
      };
    }
  );

  const educacion: Education[] = (arr(obj.educacion) as unknown[]).map((e) => {
    const x = (e ?? {}) as Record<string, unknown>;
    return {
      titulo: str(x.titulo),
      institucion: str(x.institucion),
      fecha_fin: str(x.fecha_fin),
      descripcion: str(x.descripcion),
    };
  });

  const hab = (obj.habilidades as Record<string, unknown> | undefined) ?? {};
  const habilidades: Skills = {
    tecnicas: arr(hab.tecnicas),
    blandas: arr(hab.blandas),
    idiomas: arr(hab.idiomas),
    tecnologias: arr(hab.tecnologias),
  };

  const proyectos: Project[] = (arr(obj.proyectos) as unknown[]).map((p) => {
    const x = (p ?? {}) as Record<string, unknown>;
    return {
      nombre: str(x.nombre),
      rol: str(x.rol),
      tecnologias: arr(x.tecnologias),
      url: str(x.url),
      descripcion: str(x.descripcion),
    };
  });

  const certificaciones: Certification[] = (
    arr(obj.certificaciones) as unknown[]
  ).map((c) => {
    const x = (c ?? {}) as Record<string, unknown>;
    return {
      nombre: str(x.nombre),
      institucion: str(x.institucion),
      fecha: str(x.fecha),
    };
  });

  const fortalezas: Fortaleza[] = (arr(obj.fortalezas) as unknown[]).map((f) => {
    const x = (f ?? {}) as Record<string, unknown>;
    return { nombre: str(x.nombre), descripcion: str(x.descripcion) };
  });

  const recursos = (obj.recursos_actuales as Record<string, unknown> | undefined) ?? {};
  const recursos_actuales: Recurso = {
    cv_existente: Boolean(recursos.cv_existente),
    texto_cv: str(recursos.texto_cv),
    links: arr(recursos.links),
  };

  const restr = (obj.restricciones as Record<string, unknown> | undefined) ?? {};
  const restricciones: Restricciones = {
    extension_maxima_paginas: Number(restr.extension_maxima_paginas) || 1,
    formato_solicitado: str(restr.formato_solicitado) || "PDF",
    otro: str(restr.otro),
  };

  return {
    meta,
    certificaciones,
    fortalezas,
    perfil_profesional,
    experiencia,
    educacion,
    habilidades,
    proyectos,
    recursos_actuales,
    restricciones,
    dudas_pendientes: arr(obj.dudas_pendientes),
  };
}

function str(v: unknown): string {
  return typeof v === "string" ? v : "";
}

function arr(v: unknown): string[] {
  if (Array.isArray(v)) return v.filter((x): x is string => typeof x === "string");
  return [];
}

// ── Completion % (para el badge en el dashboard) ────────────────────────

/** Score 0-100 de "cuán completo está" el CV. Heurística simple. */
export function completionPercent(ctx: CVContext): number {
  let filled = 0;
  let total = 0;

  const m = ctx.meta;
  total += 1;
  if (m.nombre_completo.trim()) filled += 1;

  total += 1;
  if (m.titulo_profesional.trim()) filled += 1;

  const c = m.contacto;
  total += 1;
  if (c.email.trim() || c.telefono.trim() || c.linkedin.trim()) filled += 1;

  total += 1;
  if (m.objetivo_cv.trim()) filled += 1;

  total += 1;
  if (ctx.experiencia.length > 0) filled += 1;

  total += 1;
  if (ctx.educacion.length > 0) filled += 1;

  total += 1;
  const h = ctx.habilidades;
  if (h.tecnicas.length || h.blandas.length || h.idiomas.length) filled += 1;

  return Math.round((filled / total) * 100);
}
