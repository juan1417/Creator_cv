// Lógica de la página principal: lista de CVs, crear, eliminar, export/import.

(function () {
  const listEl = document.getElementById("cv-list");
  const emptyEl = document.getElementById("empty-state");
  const formNew = document.getElementById("form-new");
  const inputTitle = document.getElementById("title");
  const btnExport = document.getElementById("btn-export");
  const btnImport = document.getElementById("btn-import");
  const fileImport = document.getElementById("file-import");
  const indicator = document.getElementById("storage-indicator");

  if (indicator) {
    const available = Storage.isAvailable();
    indicator.textContent = available ? "localStorage" : "localStorage no disponible";
    indicator.title = available
      ? "Los CVs se guardan en este navegador (localStorage)"
      : "Tu navegador bloqueó localStorage. Los datos no se podrán guardar.";
    if (!available) indicator.style.color = "var(--danger-fg)";
  }

  function render() {
    const cvs = CvStore.list();
    listEl.innerHTML = "";
    if (cvs.length === 0) {
      emptyEl.classList.remove("hidden");
      return;
    }
    emptyEl.classList.add("hidden");
    for (const cv of cvs) {
      const li = document.createElement("li");
      li.innerHTML = `
        <a href="/cv-edit.html?id=${encodeURIComponent(cv.id)}">${Shared.escapeHtml(cv.title || "Sin título")}</a>
        <span class="meta-muted">actualizado ${Shared.formatDate(cv.updated_at)}</span>
        <button type="button" class="btn btn-danger btn-compact" data-action="delete" data-id="${cv.id}">Eliminar</button>
      `;
      listEl.appendChild(li);
    }
  }

  listEl.addEventListener("click", (e) => {
    const btn = e.target.closest('[data-action="delete"]');
    if (!btn) return;
    const id = btn.getAttribute("data-id");
    const cv = CvStore.get(id);
    if (!cv) return;
    if (!confirm(`¿Eliminar "${cv.title || "Sin título"}"? Se borrará del navegador. No se puede deshacer.`)) return;
    CvStore.remove(id);
    Shared.flash("CV eliminado", "success");
    render();
  });

  formNew.addEventListener("submit", (e) => {
    e.preventDefault();
    try {
      const title = inputTitle.value.trim();
      console.log("[home] creando CV con título:", title);
      if (!Storage.isAvailable()) {
        Shared.flash("Tu navegador bloqueó localStorage. Habilitá cookies/storage y recargá.", "error");
        return;
      }
      const cv = CvStore.create({ title });
      console.log("[home] CV creado:", cv.id, cv.title);
      inputTitle.value = "";
      Shared.flash(`CV "${cv.title}" creado`, "success");
      // Damos tiempo al flash a renderizarse antes de navegar
      setTimeout(() => {
        // Usamos query string en vez de path: el path puede ser normalizado
        // por Vercel/CDN y perder el id. ?id= siempre se preserva.
        window.location.href = `/cv-edit.html?id=${encodeURIComponent(cv.id)}`;
      }, 50);
    } catch (err) {
      console.error("[home] error al crear CV:", err);
      Shared.flash("Error al crear el CV: " + (err.message || err), "error");
    }
  });

  btnExport.addEventListener("click", () => {
    const data = Storage.exportAll();
    const text = JSON.stringify(data, null, 2);
    const stamp = new Date().toISOString().slice(0, 10);
    Shared.downloadText(text, `creator-cv-backup-${stamp}.json`, "application/json");
  });

  btnImport.addEventListener("click", () => fileImport.click());

  fileImport.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      // Detectar formato:
      //  - Backup completo localStorage: { "cvs:index": [...], "cvs:<id>": {...}, ... }
      //  - export_to_json.py: { "version": 1, "cvs": [{title, context_json, ...}], ... }
      const isFullBackup = Object.keys(data).some((k) => k.startsWith("cvs:"));
      const isExport = Array.isArray(data.cvs);

      if (isFullBackup) {
        if (!confirm("Vas a REEMPLAZAR todos los CVs locales con los del archivo. ¿Continuar?")) {
          fileImport.value = "";
          return;
        }
        const n = CvImporter.importFromFullBackup(data);
        Shared.flash(`Importados ${n} CV del backup. Recargando…`, "success");
        setTimeout(() => window.location.reload(), 800);
      } else if (isExport) {
        if (!confirm(`Vas a importar ${data.cvs.length} CV del archivo. ¿Continuar?`)) {
          fileImport.value = "";
          return;
        }
        const n = CvImporter.importFromExport(data);
        Shared.flash(`Importados ${n} CV. Recargando…`, "success");
        setTimeout(() => window.location.reload(), 800);
      } else {
        throw new Error("Formato no reconocido. Tiene que ser un backup de localStorage o un export del script export_to_json.py.");
      }
    } catch (err) {
      Shared.flash(`No se pudo importar: ${err.message}`, "error");
    } finally {
      fileImport.value = "";
    }
  });

  // ── Sync con el backend (Flask) ──
  const btnSync = document.getElementById("btn-sync");
  const btnSyncCheck = document.getElementById("btn-sync-check");
  const syncResult = document.getElementById("sync-result");
  const syncStatus = document.getElementById("sync-status");

  async function checkBackend() {
    const ok = await ApiClient.health();
    if (ok) {
      syncResult.textContent = "✓ Servidor disponible. Listo para sincronizar.";
      syncResult.style.color = "var(--color-soft-indigo)";
    } else {
      syncResult.textContent = "✗ No se pudo conectar con el servidor. ¿Está deployado el Flask?";
      syncResult.style.color = "var(--danger-fg)";
    }
    return ok;
  }

  btnSyncCheck.addEventListener("click", async () => {
    syncResult.textContent = "Verificando…";
    await checkBackend();
  });

  btnSync.addEventListener("click", async () => {
    if (!(await checkBackend())) return;
    btnSync.disabled = true;
    btnSync.classList.add("is-loading");
    const original = btnSync.textContent;
    btnSync.textContent = "Sincronizando…";
    syncResult.textContent = "Push + pull en curso…";
    syncResult.style.color = "var(--color-ash)";
    try {
      const r = await CvSync.syncAll();
      const parts = [];
      if (r.pushed) parts.push(`${r.pushed} empujados`);
      if (r.pulled) parts.push(`${r.pulled} traídos`);
      if (r.push_failed) parts.push(`${r.push_failed} fallaron`);
      syncResult.textContent = `✓ Sincronización OK (${r.duration_ms}ms). ${parts.join(", ") || "sin cambios"}.`;
      syncResult.style.color = "var(--color-soft-indigo)";
      render();
    } catch (e) {
      syncResult.textContent = "✗ " + e.message;
      syncResult.style.color = "var(--danger-fg)";
    } finally {
      btnSync.disabled = false;
      btnSync.classList.remove("is-loading");
      btnSync.textContent = original;
    }
  });

  // Check inicial silencioso
  checkBackend().then((ok) => {
    if (!ok) {
      syncResult.textContent = "El servidor no responde. localStorage sigue funcionando.";
      syncResult.style.color = "var(--color-ash)";
    }
  });

  render();
})();
