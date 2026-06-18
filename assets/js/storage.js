// Capa de abstracción sobre localStorage.
// Aísla el resto de la app de la API del navegador para poder migrar a
// IndexedDB en el futuro sin tocar los consumidores.

const Storage = (() => {
  const NS = "creator_cv:";

  function isAvailable() {
    try {
      const t = "__test__";
      localStorage.setItem(t, t);
      localStorage.removeItem(t);
      return true;
    } catch {
      return false;
    }
  }

  function get(key, fallback = null) {
    try {
      const raw = localStorage.getItem(NS + key);
      return raw == null ? fallback : JSON.parse(raw);
    } catch (e) {
      console.warn(`[storage] get(${key}) falló:`, e);
      return fallback;
    }
  }

  function set(key, value) {
    try {
      localStorage.setItem(NS + key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.error(`[storage] set(${key}) falló:`, e);
      return false;
    }
  }

  function remove(key) {
    localStorage.removeItem(NS + key);
  }

  function listKeys() {
    const out = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(NS)) out.push(k.slice(NS.length));
    }
    return out;
  }

  function exportAll() {
    const data = {};
    for (const k of listKeys()) {
      data[k] = get(k);
    }
    return data;
  }

  function importAll(data, { merge = false } = {}) {
    if (!merge) {
      for (const k of listKeys()) remove(k);
    }
    for (const [k, v] of Object.entries(data)) {
      set(k, v);
    }
  }

  return { isAvailable, get, set, remove, listKeys, exportAll, importAll };
})();

window.Storage = Storage;
