// Definición de los pasos del asistente local.
// Cada paso sabe: id, título, qué datos recoge, cómo los guarda en el JSON del CV.
// Equivalente JS de creator_cv.interview.

const InterviewFlow = (() => {
  const STEPS = [
    {
      id: "meta",
      title: "Datos generales y contacto",
      lede: "Idioma, cómo te presentás en el CV (nombre y título) y forma de contacto opcional.",
      questions: [
        "Tu nombre completo y un título profesional corto.",
        "Idioma del CV (para el texto que verá quien lo lea).",
        "Datos de contacto (email, teléfono, LinkedIn, ubicación).",
      ],
      fields: [
        { name: "nombre_completo", label: "Nombre completo", type: "text" },
        { name: "titulo_profesional", label: "Título profesional", type: "text", hint: "Ej. Desarrollador backend, Diseñador UX, etc." },
        { name: "idioma_cv", label: "Idioma del CV", type: "select", options: [
          { value: "español", label: "Español" },
          { value: "inglés", label: "Inglés" },
          { value: "portugués", label: "Portugués" },
          { value: "francés", label: "Francés" },
          { value: "alemán", label: "Alemán" },
        ]},
        { name: "email", label: "Email", type: "email", autocomplete: "email" },
        { name: "telefono", label: "Teléfono", type: "tel", autocomplete: "tel" },
        { name: "linkedin", label: "LinkedIn (URL o usuario)", type: "url", placeholder: "https://linkedin.com/in/..." },
        { name: "ubicacion_contacto", label: "Ubicación", type: "text", hint: "Ciudad, país" },
      ],
      apply(data, form) {
        const m = data.meta = data.meta || {};
        m.nombre_completo = (form.get("nombre_completo") || "").trim();
        m.titulo_profesional = (form.get("titulo_profesional") || "").trim();
        m.idioma_cv = (form.get("idioma_cv") || "").trim();
        m.contacto = m.contacto || {};
        m.contacto.email = (form.get("email") || "").trim();
        m.contacto.telefono = (form.get("telefono") || "").trim();
        m.contacto.linkedin = (form.get("linkedin") || "").trim();
        m.contacto.ubicacion = (form.get("ubicacion_contacto") || "").trim();
      },
      load(data) {
        const m = data.meta || {};
        const c = m.contacto || {};
        return {
          nombre_completo: m.nombre_completo || "",
          titulo_profesional: m.titulo_profesional || "",
          idioma_cv: m.idioma_cv || "español",
          email: c.email || "",
          telefono: c.telefono || "",
          linkedin: c.linkedin || "",
          ubicacion_contacto: c.ubicacion || "",
        };
      },
    },
    {
      id: "perfil",
      title: "Perfil profesional",
      lede: "Un párrafo corto (3-5 líneas) que resuma quién sos y qué buscás.",
      fields: [
        { name: "resumen", label: "Resumen del perfil", type: "textarea", hint: "3-5 líneas. Qué hacés, en qué destacás, qué buscás." },
      ],
      apply(data, form) {
        const p = data.perfil_profesional = data.perfil_profesional || {};
        p.resumen = (form.get("resumen") || "").trim();
      },
      load(data) {
        return { resumen: (data.perfil_profesional || {}).resumen || "" };
      },
    },
    {
      id: "experiencia",
      title: "Experiencia laboral",
      lede: "Tu experiencia más relevante. Una entrada por puesto.",
      fields: [
        { name: "empresa", label: "Empresa", type: "text" },
        { name: "cargo", label: "Cargo", type: "text" },
        { name: "ubicacion", label: "Ubicación", type: "text" },
        { name: "fecha_inicio", label: "Fecha de inicio", type: "month" },
        { name: "fecha_fin", label: "Fecha de fin (vacío si es el actual)", type: "month" },
        { name: "responsabilidades", label: "Responsabilidades (una por línea)", type: "textarea" },
        { name: "logros", label: "Logros (una por línea)", type: "textarea" },
      ],
      apply(data, form) {
        data.experiencia = data.experiencia || [];
        data.experiencia.push({
          empresa: (form.get("empresa") || "").trim(),
          cargo: (form.get("cargo") || "").trim(),
          ubicacion: (form.get("ubicacion") || "").trim(),
          fecha_inicio: (form.get("fecha_inicio") || "").trim(),
          fecha_fin: (form.get("fecha_fin") || "").trim(),
          actual: !(form.get("fecha_fin") || "").trim(),
          responsabilidades: (form.get("responsabilidades") || "").split("\n").map((s) => s.trim()).filter(Boolean),
          logros: (form.get("logros") || "").split("\n").map((s) => s.trim()).filter(Boolean),
        });
      },
      allow_skip: true,
      only_continue: false,
      show_count: true,
    },
    {
      id: "educacion",
      title: "Educación",
      lede: "Tu formación principal.",
      fields: [
        { name: "institucion", label: "Institución", type: "text" },
        { name: "titulo", label: "Título", type: "text" },
        { name: "fecha_inicio", label: "Fecha de inicio", type: "month" },
        { name: "fecha_fin", label: "Fecha de fin", type: "month" },
        { name: "estado", label: "Estado", type: "select", options: [
          { value: "completo", label: "Completo" },
          { value: "en curso", label: "En curso" },
          { value: "incompleto", label: "Incompleto" },
          { value: "pausado", label: "Pausado" },
        ]},
      ],
      apply(data, form) {
        data.educacion = data.educacion || [];
        data.educacion.push({
          institucion: (form.get("institucion") || "").trim(),
          titulo: (form.get("titulo") || "").trim(),
          fecha_inicio: (form.get("fecha_inicio") || "").trim(),
          fecha_fin: (form.get("fecha_fin") || "").trim(),
          estado: (form.get("estado") || "").trim(),
        });
      },
      allow_skip: true,
      show_count: true,
    },
    {
      id: "habilidades",
      title: "Habilidades",
      lede: "Tus habilidades técnicas, blandas e idiomas. Una por línea.",
      fields: [
        { name: "tecnicas", label: "Técnicas (lenguajes, frameworks, herramientas)", type: "textarea" },
        { name: "blandas", label: "Blandas", type: "textarea" },
        { name: "idiomas", label: "Idiomas (ej. Inglés B1, Español nativo)", type: "textarea" },
      ],
      apply(data, form) {
        const h = data.habilidades = data.habilidades || {};
        h.tecnicas = (form.get("tecnicas") || "").split("\n").map((s) => s.trim()).filter(Boolean);
        h.blandas = (form.get("blandas") || "").split("\n").map((s) => s.trim()).filter(Boolean);
        h.idiomas = (form.get("idiomas") || "").split("\n").map((s) => s.trim()).filter(Boolean);
      },
      load(data) {
        const h = data.habilidades || {};
        return {
          tecnicas: (h.tecnicas || []).join("\n"),
          blandas: (h.blandas || []).join("\n"),
          idiomas: (h.idiomas || []).join("\n"),
        };
      },
    },
    {
      id: "proyectos",
      title: "Proyectos",
      lede: "Proyectos personales o profesionales que querés destacar.",
      fields: [
        { name: "nombre", label: "Nombre del proyecto", type: "text" },
        { name: "descripcion", label: "Descripción", type: "textarea" },
        { name: "tecnologias", label: "Tecnologías (separadas por coma)", type: "text" },
        { name: "enlace", label: "Enlace (GitHub, demo, etc.)", type: "url" },
      ],
      apply(data, form) {
        data.proyectos = data.proyectos || [];
        data.proyectos.push({
          nombre: (form.get("nombre") || "").trim(),
          descripcion: (form.get("descripcion") || "").trim(),
          tecnologias: (form.get("tecnologias") || "").split(",").map((s) => s.trim()).filter(Boolean),
          enlace: (form.get("enlace") || "").trim(),
        });
      },
      allow_skip: true,
      show_count: true,
    },
    {
      id: "recursos",
      title: "Recursos actuales",
      lede: "Si tenés un CV previo o links útiles, los podés pegar acá para no perderlos.",
      fields: [
        { name: "cv_existente", label: "Tengo un CV previo pegado abajo", type: "checkbox" },
        { name: "texto_cv", label: "Texto del CV previo (opcional)", type: "textarea" },
        { name: "links", label: "Links (uno por línea — LinkedIn, portafolio, etc.)", type: "textarea" },
      ],
      apply(data, form) {
        const r = data.recursos_actuales = data.recursos_actuales || {};
        r.cv_existente = form.get("cv_existente") === "1";
        r.texto_cv = (form.get("texto_cv") || "").trim();
        r.links = (form.get("links") || "").split("\n").map((s) => s.trim()).filter(Boolean);
      },
      allow_skip: true,
    },
    {
      id: "restricciones",
      title: "Restricciones",
      lede: "Si tenés un límite de páginas, formato pedido, o dudas, anotalas acá.",
      fields: [
        { name: "extension_maxima_paginas", label: "Extensión máxima (páginas)", type: "number", min: 1, max: 10 },
        { name: "formato_solicitado", label: "Formato solicitado", type: "select", options: [
          { value: "PDF", label: "PDF" },
          { value: "DOCX", label: "Word (.docx)" },
          { value: "ambos", label: "Ambos" },
        ]},
        { name: "otro", label: "Otro (notas adicionales)", type: "textarea" },
      ],
      apply(data, form) {
        const r = data.restricciones = data.restricciones || {};
        const ext = parseInt(form.get("extension_maxima_paginas") || "0", 10);
        r.extension_maxima_paginas = (ext >= 1 && ext <= 10) ? ext : 1;
        r.formato_solicitado = (form.get("formato_solicitado") || "PDF").trim();
        r.otro = (form.get("otro") || "").trim();
      },
      load(data) {
        const r = data.restricciones || {};
        return {
          extension_maxima_paginas: r.extension_maxima_paginas || 1,
          formato_solicitado: r.formato_solicitado || "PDF",
          otro: r.otro || "",
        };
      },
    },
  ];

  function indexOf(id) { return STEPS.findIndex((s) => s.id === id); }
  function get(id) { return STEPS[indexOf(id)]; }
  function next(id) { return STEPS[indexOf(id) + 1]; }
  function prev(id) { return STEPS[indexOf(id) - 1]; }
  function first() { return STEPS[0]; }
  function all() { return STEPS; }

  return { all, get, next, prev, first, indexOf };
})();

window.InterviewFlow = InterviewFlow;
