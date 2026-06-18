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
        <a href="/cvs/${encodeURIComponent(cv.id)}/edit">${Shared.escapeHtml(cv.title || "Sin título")}</a>
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
    const title = inputTitle.value.trim();
    const cv = CvStore.create({ title });
    inputTitle.value = "";
    Shared.flash(`CV "${cv.title}" creado`, "success");
    window.location.href = `/cvs/${encodeURIComponent(cv.id)}/edit`;
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

  render();
})();
