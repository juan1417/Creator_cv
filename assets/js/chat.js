// Chat con Gemini vía /api/gemini (Vercel serverless function).
// El historial se guarda en localStorage (clave: chats:<cv_id>).

(function () {
  const id = Shared.getCvId();
  if (!id) { Shared.flash("Falta el id del CV.", "error"); return; }
  const cv = CvStore.get(id);
  if (!cv) { Shared.flash("No se encontró el CV en este navegador.", "error"); return; }

  document.getElementById("back-link").href = `/cv-edit.html?id=${encodeURIComponent(id)}`;
  document.getElementById("bc-edit").href = `/cv-edit.html?id=${encodeURIComponent(id)}`;
  document.getElementById("link-edit").href = `/cv-edit.html?id=${encodeURIComponent(id)}`;
  document.getElementById("link-preview").href = `/cv-preview.html?id=${encodeURIComponent(id)}`;
  document.title = `Chat IA · ${cv.title || "CV"}`;

  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const send = document.getElementById("chat-send");
  const cap = document.getElementById("user_capacity");
  const banner = document.getElementById("chat-patch-banner");
  const btnApply = document.getElementById("btn-apply");
  const btnClear = document.getElementById("btn-clear");

  const chatKey = `chats:${id}`;
  function loadChat() { return Storage.get(chatKey, { messages: [] }); }
  function saveChat(c) { Storage.set(chatKey, c); }

  function render() {
    const c = loadChat();
    log.innerHTML = "";
    for (const m of c.messages) {
      const wrap = document.createElement("div");
      wrap.className = "chat-msg chat-msg--" + (m.role === "user" ? "user" : "assistant");
      const lab = document.createElement("span");
      lab.className = "chat-msg__label";
      lab.textContent = m.role === "user" ? "Tú" : "Asistente";
      const body = document.createElement("div");
      body.className = "chat-msg__body";
      body.textContent = m.content;
      wrap.appendChild(lab);
      wrap.appendChild(body);
      if (m.patch) {
        const meta = document.createElement("p");
        meta.className = "chat-msg__meta meta-muted";
        meta.textContent = "Incluye parche JSON guardado — usá «Aplicar última sugerencia».";
        wrap.appendChild(meta);
      }
      log.appendChild(wrap);
    }
    log.scrollTop = log.scrollHeight;

    const c2 = loadChat();
    const last = c2.messages[c2.messages.length - 1];
    if (last && last.patch) banner.classList.remove("hidden");
    else banner.classList.add("hidden");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = (input.value || "").trim();
    if (!text) return;
    send.disabled = true;
    send.classList.add("is-loading");
    const original = send.textContent;
    send.textContent = "Enviando…";
    banner.classList.add("hidden");

    // append user msg
    const c = loadChat();
    c.messages.push({ role: "user", content: text });
    saveChat(c);
    input.value = "";
    render();

    try {
      const data = await ApiClient.gemini({
        messages: c.messages,
        user_capacity: cap.value,
        cv_context: CvStore.parseContext(cv),
      });
      if (!data || !data.ok) {
        const msg = (data && data.error) || "Error desconocido";
        const c2 = loadChat();
        c2.messages.push({ role: "assistant", content: "Error: " + msg });
        saveChat(c2);
        render();
        return;
      }
      const c3 = loadChat();
      const lastMsg = { role: "assistant", content: data.assistant || "" };
      if (data.patch) lastMsg.patch = data.patch;
      c3.messages.push(lastMsg);
      saveChat(c3);
      render();
    } catch (err) {
      const c2 = loadChat();
      c2.messages.push({ role: "assistant", content: "No se pudo conectar con el servidor: " + (err.message || err) });
      saveChat(c2);
      render();
    } finally {
      send.disabled = false;
      send.classList.remove("is-loading");
      send.textContent = original;
      input.focus();
    }
  });

  btnApply.addEventListener("click", () => {
    const c = loadChat();
    const last = c.messages[c.messages.length - 1];
    if (!last || !last.patch) { Shared.flash("No hay parche para aplicar.", "info"); return; }
    const current = CvStore.parseContext(cv);
    const merged = _mergePatch(current, last.patch);
    CvStore.saveContext(id, merged);
    Shared.flash("Parche aplicado al CV.", "success");
    setTimeout(() => window.location.href = `/cv-edit.html?id=${encodeURIComponent(id)}#chat-log`, 400);
  });

  btnClear.addEventListener("click", () => {
    if (!confirm("¿Borrar todo el historial de este chat?")) return;
    saveChat({ messages: [] });
    render();
    Shared.flash("Historial vaciado", "info");
  });

  // Merge profundo simple: el patch tiene la misma forma que el contexto;
  // solo sobreescribe claves presentes.
  function _mergePatch(base, patch) {
    if (typeof patch !== "object" || patch === null) return base;
    const out = Array.isArray(base) ? [...base] : { ...(base || {}) };
    for (const [k, v] of Object.entries(patch)) {
      if (v && typeof v === "object" && !Array.isArray(v)) {
        out[k] = _mergePatch(out[k] || {}, v);
      } else {
        out[k] = v;
      }
    }
    return out;
  }

  render();
})();
