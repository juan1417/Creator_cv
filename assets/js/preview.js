// Lógica de la vista previa: render del CV en HTML (plantilla Harvard) + MD.

(function () {
  const id = Shared.getQueryParam("id");
  if (!id) {
    Shared.flash("Falta el id del CV.", "error");
    return;
  }
  const cv = CvStore.get(id);
  if (!cv) {
    Shared.flash("No se encontró el CV en este navegador.", "error");
    return;
  }

  const root = document.getElementById("preview-root");
  const mdPre = document.getElementById("md-source");
  const back = document.getElementById("back-link");
  const bcEdit = document.getElementById("bc-edit");

  back.href = `/cvs/${encodeURIComponent(id)}/edit`;
  bcEdit.href = `/cvs/${encodeURIComponent(id)}/edit`;
  document.title = `Vista previa · ${cv.title || "CV"}`;

  const data = CvStore.parseContext(cv);
  const html = CvRender.toPreviewHtml(data, cv.title);
  const isEmpty = !html || html.length < 200;

  if (isEmpty) {
    root.innerHTML = `
      <p class="cv-preview-empty">Ahora mismo no hay texto que mostrar: el contexto JSON está vacío o todos los campos van sin contenido.</p>
      <p class="cv-preview-hint">Completá datos en el <a href="/cvs/${encodeURIComponent(id)}/edit">editor</a> y volvé a abrir la vista previa.</p>
    `;
  } else {
    root.innerHTML = html;
  }

  const md = CvRender.toMarkdown(data);
  mdPre.textContent = md.trim() || "(vacío)";
})();
