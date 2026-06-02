/* Creator CV — form interactivity
 *
 *  - Clone <template> items for experiencia / educacion / proyectos
 *  - Chip add/remove for habilidades / certificaciones / fortalezas
 *  - Populate items from existing CV dict (server-rendered via JSON
 *    injected in a <script type="application/json"> below the form)
 *  - "Adapt with AI" button posts the form via fetch to /adapt
 */

(function () {
  "use strict";

  // --- Initial data (server-injected) -------------------------------------
  const dataEl = document.getElementById("cv-initial-data");
  const initialData = dataEl ? JSON.parse(dataEl.textContent) : null;

  const form = document.getElementById("cv-form");
  if (!form) return;

  // --- Loading overlay helper ---------------------------------------------
  const overlay = document.getElementById("loading-overlay");
  const loadingTitle = document.getElementById("loading-title");
  const loadingMessage = document.getElementById("loading-message");

  function showOverlay(title, message) {
    if (!overlay) return;
    if (title && loadingTitle) loadingTitle.textContent = title;
    if (message && loadingMessage) loadingMessage.textContent = message;
    overlay.setAttribute("data-active", "true");
  }

  function hideOverlay() {
    if (!overlay) return;
    overlay.setAttribute("data-active", "false");
  }

  function setButtonPending(btn, pendingLabel) {
    if (!btn) return;
    btn._origLabel = btn._origLabel || btn.textContent;
    btn.disabled = true;
    btn.textContent = pendingLabel || "Procesando…";
  }

  function restoreButton(btn) {
    if (!btn) return;
    btn.disabled = false;
    if (btn._origLabel) btn.textContent = btn._origLabel;
  }

  // Bind a single form submit (sync) to show the overlay.
  function bindFormOverlay(formEl, defaultBtn) {
    if (!formEl) return;
    if (formEl.dataset.loading !== "true") return;
    formEl.addEventListener("submit", () => {
      const title = formEl.dataset.loadingTitle || "Procesando…";
      const message = formEl.dataset.loadingMessage || "Esto puede tardar unos segundos.";
      showOverlay(title, message);
      if (defaultBtn) {
        const lbl = defaultBtn.dataset.defaultLabel || defaultBtn.textContent;
        setButtonPending(defaultBtn, "⏳ " + (lbl.replace(/^[^\s]+\s/, "") || lbl));
      }
    });
  }

  // The cv_form.html and cv_import.html forms use different ids; bind both.
  const importForm = document.querySelector('form[enctype="multipart/form-data"]');
  const importBtn = importForm && importForm.querySelector('button[type="submit"]');
  bindFormOverlay(importForm, importBtn);

  // --- Section items (experiencia / educacion / proyectos) ----------------
  const SECTION_TPLS = {
    experiencia: "tpl-experiencia",
    educacion: "tpl-educacion",
    proyectos: "tpl-proyectos",
  };

  function nextIndex(listEl) {
    return listEl.querySelectorAll(".item").length;
  }

  function addItem(section, values) {
    const tpl = document.getElementById(SECTION_TPLS[section]);
    if (!tpl) return;
    const list = document.getElementById(`${section}-list`);
    if (!list) return;
    const idx = nextIndex(list);
    const node = tpl.content.cloneNode(true);
    // Replace __IDX__ with the actual index in all name= attributes.
    node.querySelectorAll("[name]").forEach((el) => {
      el.setAttribute("name", el.getAttribute("name").replace("__IDX__", String(idx)));
    });
    list.appendChild(node);
    if (values) fillItem(list.lastElementChild, section, values);
  }

  function fillItem(itemEl, section, values) {
    if (section === "experiencia") {
      setVal(itemEl, 'input[name*="[cargo]"]', values.cargo);
      setVal(itemEl, 'input[name*="[empresa]"]', values.empresa);
      setVal(itemEl, 'input[name*="[ubicacion]"]', values.ubicacion);
      setVal(itemEl, 'input[name*="[fecha_inicio]"]', values.fecha_inicio);
      setVal(itemEl, 'input[name*="[fecha_fin]"]', values.fecha_fin);
      const ck = itemEl.querySelector('input[type="checkbox"][name*="[actual]"]');
      if (ck) ck.checked = !!values.actual;
      setVal(itemEl, 'textarea[name*="[responsabilidades]"]', (values.responsabilidades || []).join("\n"));
      setVal(itemEl, 'textarea[name*="[logros]"]', (values.logros || []).join("\n"));
    } else if (section === "educacion") {
      setVal(itemEl, 'input[name*="[institucion]"]', values.institucion);
      setVal(itemEl, 'input[name*="[titulo]"]', values.titulo);
      setVal(itemEl, 'input[name*="[ubicacion]"]', values.ubicacion);
      setVal(itemEl, 'input[name*="[estado]"]', values.estado);
      setVal(itemEl, 'input[name*="[fecha_inicio]"]', values.fecha_inicio);
      setVal(itemEl, 'input[name*="[fecha_fin]"]', values.fecha_fin);
    } else if (section === "proyectos") {
      setVal(itemEl, 'input[name*="[nombre]"]', values.nombre);
      setVal(itemEl, 'textarea[name*="[descripcion]"]', values.descripcion);
      setVal(itemEl, 'input[name*="[tecnologias]"]', (values.tecnologias || []).join(", "));
      setVal(itemEl, 'input[name*="[enlace]"]', values.enlace);
    }
  }

  function setVal(scope, selector, value) {
    const el = scope.querySelector(selector);
    if (el != null && (value || value === 0)) el.value = value;
  }

  // Wire "+ Añadir" buttons
  document.querySelectorAll("[data-add]").forEach((btn) => {
    btn.addEventListener("click", () => addItem(btn.dataset.add));
  });

  // Wire "Eliminar" inside items (event delegation)
  form.addEventListener("click", (ev) => {
    const t = ev.target.closest("[data-remove-item]");
    if (t) {
      const item = t.closest(".item");
      if (item) item.remove();
    }
  });

  // --- Chips ---------------------------------------------------------------
  function addChip(container, name, value) {
    const span = document.createElement("span");
    span.className = "chip";
    span.appendChild(document.createTextNode(value));
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "×";
    btn.dataset.remove = "";
    const hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = name;
    hidden.value = value;
    span.appendChild(btn);
    span.appendChild(hidden);
    container.appendChild(span);
  }

  form.addEventListener("click", (ev) => {
    const rm = ev.target.closest(".chip [data-remove]");
    if (rm) {
      const chip = rm.closest(".chip");
      if (chip) chip.remove();
    }
  });

  form.querySelectorAll("input[data-chip-input]").forEach((input) => {
    input.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        const value = input.value.trim();
        if (!value) return;
        const targetName = input.dataset.chipInput;
        const container = form.querySelector(`.chips[data-chips="${targetName}"]`);
        if (container) {
          addChip(container, targetName, value);
          input.value = "";
        }
      }
    });
  });

  // --- Populate from initial data -----------------------------------------
  if (initialData) {
    (initialData.experiencia || []).forEach((v) => addItem("experiencia", v));
    (initialData.educacion || []).forEach((v) => addItem("educacion", v));
    (initialData.proyectos || []).forEach((v) => addItem("proyectos", v));
  }

  // --- Adapt with AI -------------------------------------------------------
  const adaptBtn = form.querySelector('[data-action="adapt"]');
  const reviewPanel = document.getElementById("review-panel");
  const reviewContent = document.getElementById("review-content");

  if (adaptBtn) {
    adaptBtn.addEventListener("click", async () => {
      const formData = new FormData(form);
      setButtonPending(adaptBtn, "⏳ Adaptando…");
      const title = adaptBtn.dataset.loadingTitle || "Adaptando con IA…";
      const message = adaptBtn.dataset.loadingMessage || "Esto puede tardar unos segundos.";
      showOverlay(title, message);
      try {
        const resp = await fetch(form.action.replace("/save", "/adapt"), {
          method: "POST",
          body: formData,
          headers: { Accept: "application/json" },
        });
        const json = await resp.json();
        if (!resp.ok || !json.ok) {
          alert(json.error || "Error al adaptar el CV.");
          return;
        }
        // Show loop result in overlay before re-rendering form
        const loop = json.loop || {};
        const reached = loop.reached_target;
        const finalScore = json.match_score || loop.final_score || 0;
        const target = loop.target_score || 70;
        const iters = loop.iterations || 1;
        const scoresList = (loop.scores_per_iteration || []).join(" → ");

        if (loadingTitle) {
          loadingTitle.textContent = reached
            ? `✓ Score ${finalScore}/100 alcanzado en ${iters} iteración${iters === 1 ? "" : "es"}`
            : `⚠ Mejor score: ${finalScore}/100 (objetivo: ${target})`;
        }
        if (loadingMessage) {
          loadingMessage.textContent = reached
            ? `Trayectoria: ${scoresList}. Recargando…`
            : `Tras ${iters} iteraciones no se alcanzó ${target}/100. Se devuelve el mejor intento. Revisa las skills faltantes y considera aprenderlas. Recargando…`;
        }

        // Wait briefly so the user can read the result, then reload.
        await new Promise((r) => setTimeout(r, 1800));

        // Replace the initial data and rebuild the form (simple re-render).
        const newData = json.cv;
        // Wipe items
        ["experiencia", "educacion", "proyectos"].forEach((s) => {
          const list = document.getElementById(`${s}-list`);
          if (list) list.innerHTML = "";
        });
        // Wipe chip groups (skip server-rendered ones with initial data)
        form.querySelectorAll(".chips").forEach((c) => (c.innerHTML = ""));
        (newData.experiencia || []).forEach((v) => addItem("experiencia", v));
        (newData.educacion || []).forEach((v) => addItem("educacion", v));
        (newData.proyectos || []).forEach((v) => addItem("proyectos", v));

        // Scalar fields
        setVal(form, 'input[name="meta.nombre_completo"]', newData.meta?.nombre_completo);
        setVal(form, 'input[name="meta.titulo_profesional"]', newData.meta?.titulo_profesional);
        const c = newData.meta?.contacto || {};
        setVal(form, 'input[name="meta.contacto.email"]', c.email);
        setVal(form, 'input[name="meta.contacto.telefono"]', c.telefono);
        setVal(form, 'input[name="meta.contacto.linkedin"]', c.linkedin);
        setVal(form, 'input[name="meta.contacto.ubicacion"]', c.ubicacion);
        setVal(form, 'textarea[name="perfil_profesional.resumen"]', newData.perfil_profesional?.resumen);
        setVal(form, 'input[name="perfil_profesional.palabras_clave"]', (newData.perfil_profesional?.palabras_clave || []).join(", "));

        // Skills
        const h = newData.habilidades || {};
        ["tecnicas", "blandas", "idiomas"].forEach((g) => {
          const container = form.querySelector(`.chips[data-chips="habilidades[${g}][]"]`);
          if (container) (h[g] || []).forEach((v) => addChip(container, `habilidades[${g}][]`, v));
        });
        ["certificaciones", "fortalezas"].forEach((g) => {
          const container = form.querySelector(`.chips[data-chips="${g}[items][]"]`);
          if (container) (newData[g] || []).forEach((v) => addChip(container, `${g}[items][]`, v));
        });

        // Show review
        if (reviewPanel && reviewContent) {
          reviewContent.textContent = json.review_md || "(sin sugerencias)";
          reviewPanel.hidden = false;
        }

        // Reload to show the new match score in the dashboard badge.
        hideOverlay();
        restoreButton(adaptBtn);
        window.location.reload();
      } catch (err) {
        alert("Error de red: " + err.message);
        hideOverlay();
        restoreButton(adaptBtn);
      }
    });
  }

  // --- Improve button (no job offer needed) -----------------------------
  const improveBtn = form.querySelector('[data-action="improve"]');
  if (improveBtn) {
    improveBtn.addEventListener("click", async () => {
      const formData = new FormData(form);
      setButtonPending(improveBtn, "⏳ Mejorando…");
      const title = improveBtn.dataset.loadingTitle || "Mejorando tu CV…";
      const message = improveBtn.dataset.loadingMessage || "Esto puede tardar unos segundos.";
      showOverlay(title, message);
      try {
        const resp = await fetch(form.action.replace("/save", "/improve"), {
          method: "POST",
          body: formData,
          headers: { Accept: "application/json" },
        });
        const json = await resp.json();
        if (!resp.ok || !json.ok) {
          alert(json.error || "Error al mejorar el CV.");
          hideOverlay();
          restoreButton(improveBtn);
          return;
        }
        // Show delta result in the overlay.
        const before = json.before_score;
        const after = json.after_score;
        const delta = json.delta;
        let titleText, msgText;
        if (before !== null && after !== null && delta !== null) {
          const sign = delta >= 0 ? "+" : "";
          const emoji = delta > 0 ? "📈" : (delta < 0 ? "📉" : "➡️");
          titleText = `${emoji} ${before}/100 → ${after}/100 (${sign}${delta} pts)`;
          msgText = "Recargando para aplicar los cambios…";
        } else {
          titleText = "✓ CV mejorado";
          msgText = "Sin oferta asociada: el delta de score no se muestra. Recargando…";
        }
        if (loadingTitle) loadingTitle.textContent = titleText;
        if (loadingMessage) loadingMessage.textContent = msgText;

        // Brief pause so the user reads the result.
        await new Promise((r) => setTimeout(r, 1500));

        // Reload — the form is rebuilt server-side with the improved CV.
        window.location.reload();
      } catch (err) {
        alert("Error de red: " + err.message);
        hideOverlay();
        restoreButton(improveBtn);
      }
    });
  }

  // --- Improve buttons on the dashboard list ----------------------------
  document.querySelectorAll('[data-action="improve-dashboard"]').forEach((btn) => {
    btn.addEventListener("click", async () => {
      const cvId = btn.dataset.cvId;
      if (!cvId) return;
      const original = btn.textContent;
      setButtonPending(btn, "⏳ Mejorando…");
      showOverlay("Mejorando tu CV…", "Reescribiendo el resumen, los bullets de experiencia y reordenando habilidades.");
      try {
        const resp = await fetch(`/cv/${cvId}/improve`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
        });
        const json = await resp.json();
        if (!resp.ok || !json.ok) {
          alert(json.error || "Error al mejorar el CV.");
          hideOverlay();
          btn.textContent = original;
          return;
        }
        const before = json.before_score;
        const after = json.after_score;
        const delta = json.delta;
        if (loadingTitle && before !== null && after !== null && delta !== null) {
          const sign = delta >= 0 ? "+" : "";
          const emoji = delta > 0 ? "📈" : (delta < 0 ? "📉" : "➡️");
          loadingTitle.textContent = `${emoji} ${before}/100 → ${after}/100 (${sign}${delta} pts)`;
        } else if (loadingTitle) {
          loadingTitle.textContent = "✓ CV mejorado";
        }
        if (loadingMessage) {
          loadingMessage.textContent = "Recargando para aplicar los cambios…";
        }
        await new Promise((r) => setTimeout(r, 1500));
        window.location.reload();
      } catch (err) {
        alert("Error de red: " + err.message);
        hideOverlay();
        btn.textContent = original;
      }
    });
  });

  function getCsrfToken() {
    // Try to find CSRF token in any form on the page.
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : "";
  }

  if (reviewPanel) {
    const closeBtn = reviewPanel.querySelector('[data-action="close-review"]');
    if (closeBtn) closeBtn.addEventListener("click", () => (reviewPanel.hidden = true));
  }

  // --- Save: intercept submit, send via fetch, reload on success ---------
  const saveBtn = form.querySelector('[data-action="save"]');
  if (saveBtn) {
    form.addEventListener("submit", async (ev) => {
      // Only intercept when the submitter was a [data-action="save"] button.
      const submitter = ev.submitter;
      if (!submitter || submitter.dataset.action !== "save") {
        // Let the submit proceed normally (e.g. browser default for "Enter").
        // But still show pending UI.
        setButtonPending(saveBtn, "⏳ Guardando…");
        showOverlay("Guardando cambios…", "Un momento por favor.");
        return;
      }
      ev.preventDefault();
      setButtonPending(saveBtn, "⏳ Guardando…");
      showOverlay("Guardando cambios…", "Un momento por favor.");
      try {
        const formData = new FormData(form);
        const resp = await fetch(form.action, {
          method: "POST",
          body: formData,
          headers: { Accept: "application/json" },
        });
        const json = await resp.json().catch(() => ({}));
        if (!resp.ok || !json.ok) {
          alert(json.error || "Error al guardar el CV.");
          hideOverlay();
          restoreButton(saveBtn);
          return;
        }
        // Show a brief success overlay, then reload to reflect saved state.
        if (loadingTitle) loadingTitle.textContent = "✓ Guardado";
        if (loadingMessage) loadingMessage.textContent = "Recargando…";
        setTimeout(() => window.location.reload(), 350);
      } catch (err) {
        alert("Error de red: " + err.message);
        hideOverlay();
        restoreButton(saveBtn);
      }
    });
  }
})();
