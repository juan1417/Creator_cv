// Lógica de la página de edición: cargar el CV, editar, guardar, exportar.

(function () {
  const id = Shared.getCvId();
  if (!id) {
    Shared.flash("Falta el id del CV en la URL. Volvé al inicio.", "error");
    setTimeout(() => window.location.href = "/", 1500);
    return;
  }

  let cv = CvStore.get(id);
  if (!cv) {
    Shared.flash("No se encontró el CV en este navegador.", "error");
    setTimeout(() => window.location.href = "/", 1500);
    return;
  }

  const titleH1 = document.getElementById("cv-title");
  const titleInput = document.getElementById("title-input");
  const breadcrumbTitle = document.getElementById("breadcrumb-title");
  const textarea = document.getElementById("context_json");
  const formSave = document.getElementById("form-save");
  const status = document.getElementById("json-status");
  const linkPreview = document.getElementById("link-preview");
  const linkJobfit = document.getElementById("link-jobfit");
  const linkInterview = document.getElementById("link-interview");
  const linkChat = document.getElementById("link-chat");
  const btnDelete = document.getElementById("btn-delete");

  // Set links
  linkPreview.href = `/cvs/${encodeURIComponent(id)}/preview`;
  linkJobfit.href = `/cvs/${encodeURIComponent(id)}/job-fit`;
  linkInterview.href = `/cvs/${encodeURIComponent(id)}/interview`;
  linkChat.href = `/cvs/${encodeURIComponent(id)}/chat`;

  function refreshTitle() {
    titleH1.textContent = cv.title || "Sin título";
    breadcrumbTitle.textContent = cv.title || "Editor";
    document.title = `${cv.title || "CV"} · Editor`;
  }

  function load() {
    titleInput.value = cv.title || "";
    textarea.value = cv.context_json || "";
    refreshTitle();
    validateJson();
  }

  function validateJson() {
    try {
      const obj = JSON.parse(textarea.value);
      const keys = Object.keys(obj || {});
      status.textContent = `JSON válido (${keys.length} claves de nivel superior).`;
      status.style.color = "var(--color-soft-indigo)";
      return obj;
    } catch (e) {
      status.textContent = "JSON inválido: " + e.message;
      status.style.color = "var(--danger-fg)";
      return null;
    }
  }

  textarea.addEventListener("input", () => {
    // validar en vivo (debounced)
    clearTimeout(window.__jsonDebounce);
    window.__jsonDebounce = setTimeout(validateJson, 300);
  });

  formSave.addEventListener("submit", (e) => {
    e.preventDefault();
    const obj = validateJson();
    if (obj === null) {
      Shared.flash("Revisá el JSON antes de guardar.", "error");
      return;
    }
    const newTitle = titleInput.value.trim() || "Sin título";
    const updated = CvStore.update(id, {
      title: newTitle,
      context_json: JSON.stringify(obj, null, 2),
    });
    cv = updated;
    refreshTitle();
    textarea.value = cv.context_json;
    Shared.flash("Guardado en localStorage", "success");
  });

  btnDelete.addEventListener("click", () => {
    if (!confirm(`¿Eliminar "${cv.title || "Sin título"}"? Se borrará del navegador. No se puede deshacer.`)) return;
    CvStore.remove(id);
    Shared.flash("CV eliminado", "success");
    setTimeout(() => window.location.href = "/", 500);
  });

  // ── Exports (Descargar)
  document.querySelectorAll("[data-export]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      const kind = a.getAttribute("data-export");
      const obj = validateJson();
      if (obj === null) {
        Shared.flash("JSON inválido, no se puede exportar.", "error");
        return;
      }
      const slug = Shared.sanitizeFilename(cv.title);
      if (kind === "md") {
        const md = CvRender.toMarkdown(obj);
        Shared.downloadText(md, `${slug}.md`, "text/markdown;charset=utf-8");
      } else if (kind === "pdf") {
        try {
          const pdf = PdfGenerator.build(obj, cv.title);
          pdf.save(`${slug}.pdf`);
        } catch (err) {
          Shared.flash("Error generando PDF: " + err.message, "error");
        }
      } else if (kind === "docx") {
        // DOCX se genera como HTML envuelto en un .doc (Word lo abre).
        // Para un .docx real se necesitaría una lib (jszip + docxtemplater).
        const html = `<!doctype html><html><head><meta charset="utf-8"><title>${Shared.escapeHtml(cv.title)}</title></head><body>${CvRender.toPreviewHtml(obj, cv.title)}</body></html>`;
        Shared.downloadText(html, `${slug}.doc`, "application/msword;charset=utf-8");
        Shared.flash("DOCX básico (.doc): se abre en Word. Para .docx real se necesita backend.", "info");
      }
    });
  });

  load();
})();
