// Cliente HTTP para la API de Flask (sync opcional).
// Si la API no está disponible (offline o sin backend), las funciones
// devuelven null o lanzan errores que el caller puede ignorar.

const ApiClient = (() => {
  const BASE = "/api";
  const TIMEOUT_MS = 8000;

  async function _fetch(path, options = {}) {
    const url = BASE + path;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const res = await fetch(url, {
        ...options,
        signal: controller.signal,
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
          ...(options.headers || {}),
        },
      });
      return res;
    } finally {
      clearTimeout(timeout);
    }
  }

  async function _check(res) {
    if (!res.ok) {
      let body = null;
      try { body = await res.json(); } catch {}
      const msg = (body && body.error) || res.statusText || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return res.json();
  }

  return {
    base: BASE,

    async health() {
      try {
        const res = await _fetch("/health");
        return (await _check(res)).ok;
      } catch {
        return false;
      }
    },

    async listCvs() {
      const res = await _fetch("/cvs");
      const data = await _check(res);
      return data.cvs || [];
    },

    async createCv({ title, context_json }) {
      const res = await _fetch("/cvs", {
        method: "POST",
        body: JSON.stringify({ title, context_json }),
      });
      const data = await _check(res);
      return data.cv;
    },

    async getCv(id) {
      const res = await _fetch("/cvs/" + encodeURIComponent(id));
      const data = await _check(res);
      return data.cv;
    },

    async updateCv(id, patch) {
      const res = await _fetch("/cvs/" + encodeURIComponent(id), {
        method: "PUT",
        body: JSON.stringify(patch),
      });
      const data = await _check(res);
      return data.cv;
    },

    async deleteCv(id) {
      const res = await _fetch("/cvs/" + encodeURIComponent(id), { method: "DELETE" });
      await _check(res);
      return true;
    },

    async getChat(id) {
      const res = await _fetch("/cvs/" + encodeURIComponent(id) + "/chat");
      const data = await _check(res);
      return data.messages || [];
    },

    async saveChat(id, messages) {
      const res = await _fetch("/cvs/" + encodeURIComponent(id) + "/chat", {
        method: "POST",
        body: JSON.stringify({ messages }),
      });
      await _check(res);
      return true;
    },

    async clearChat(id) {
      const res = await _fetch("/cvs/" + encodeURIComponent(id) + "/chat", { method: "DELETE" });
      await _check(res);
      return true;
    },

    async gemini({ messages, user_capacity, cv_context }) {
      const res = await _fetch("/gemini", {
        method: "POST",
        body: JSON.stringify({ messages, user_capacity, cv_context }),
      });
      const data = await _check(res);
      return data;
    },
  };
})();

window.ApiClient = ApiClient;
