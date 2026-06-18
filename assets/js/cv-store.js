// CRUD de CVs sobre localStorage.
// Esquema de un CV: { id, title, context_json (string), created_at, updated_at }
//
// Los IDs se generan como timestamp+random para que sean únicos sin coordinación.

const CvStore = (() => {
  const KEY_INDEX = "cvs:index";
  const KEY_CV = (id) => `cvs:${id}`;

  function _index() {
    return Storage.get(KEY_INDEX, []);
  }

  function _saveIndex(idx) {
    Storage.set(KEY_INDEX, idx);
  }

  function _newId() {
    return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  }

  function list() {
    return _index()
      .map((id) => get(id))
      .filter(Boolean)
      .sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
  }

  function get(id) {
    return Storage.get(KEY_CV(id));
  }

  function create({ title = "", context_json = "" } = {}) {
    const id = _newId();
    const now = new Date().toISOString();
    const cv = {
      id,
      title: title.trim() || "Sin título",
      context_json: context_json || emptyContextJson(),
      created_at: now,
      updated_at: now,
    };
    Storage.set(KEY_CV(id), cv);
    _index().push(id);
    _saveIndex(_index());
    return cv;
  }

  function update(id, patch) {
    const cv = get(id);
    if (!cv) return null;
    const next = { ...cv, ...patch, updated_at: new Date().toISOString() };
    Storage.set(KEY_CV(id), next);
    return next;
  }

  function remove(id) {
    const idx = _index();
    const i = idx.indexOf(id);
    if (i >= 0) {
      idx.splice(i, 1);
      _saveIndex(idx);
    }
    Storage.remove(KEY_CV(id));
  }

  function emptyContextJson() {
    // Devuelve el string JSON con la estructura vacía que la app espera.
    return JSON.stringify(
      {
        meta: {
          nombre_completo: "",
          titulo_profesional: "",
          idioma_cv: "español",
          objetivo_cv: "",
          tipo_cv: "",
          nivel_seniority: "",
          contacto: { telefono: "", email: "", linkedin: "", ubicacion: "" },
        },
        certificaciones: [],
        fortalezas: [],
        perfil_profesional: { resumen: "", palabras_clave: [] },
        experiencia: [],
        educacion: [],
        habilidades: { tecnicas: [], blandas: [], idiomas: [] },
        proyectos: [],
        recursos_actuales: { cv_existente: false, texto_cv: "", links: [] },
        restricciones: { extension_maxima_paginas: 1, formato_solicitado: "PDF", otro: "" },
        dudas_pendientes: [],
      },
      null,
      2
    );
  }

  function parseContext(cv) {
    try {
      return JSON.parse(cv.context_json || emptyContextJson());
    } catch {
      return {};
    }
  }

  function saveContext(id, contextObj) {
    const text = typeof contextObj === "string"
      ? contextObj
      : JSON.stringify(contextObj, null, 2);
    return update(id, { context_json: text });
  }

  return { list, get, create, update, remove, parseContext, saveContext, emptyContextJson };
})();

window.CvStore = CvStore;
