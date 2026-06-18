// Genera un PDF con la plantilla Harvard de una columna, en negro.
// Usa jsPDF cargado por CDN (window.jspdf.jsPDF).

const PdfGenerator = (() => {
  function _e(v) { return Shared.escapeHtml(v == null ? "" : v); }
  function _fmt(s) { return s == null ? "" : String(s); }
  function _clean(u) { return CvRender._cleanUrl(u); }

  function build(data, fallbackTitle = "") {
    const { jsPDF } = window.jspdf || {};
    if (!jsPDF) throw new Error("jsPDF no está disponible");

    const pdf = new jsPDF({ unit: "mm", format: "a4" });
    const pageW = pdf.internal.pageSize.getWidth();
    const pageH = pdf.internal.pageSize.getHeight();
    const left = 18, right = pageW - 18;
    const usable = pageW - left - right;

    const meta = data.meta || {};
    const nombre = (meta.nombre_completo || "").trim() || fallbackTitle.trim();
    const contact = CvRender._contactLine ? [] : [];
    // Construimos contact manualmente (reusamos la lógica via CvRender si está)
    const contactLine = (typeof CvRender._contactLine === "function")
      ? CvRender._contactLine(meta, data)
      : _contactLineLocal(meta, data);

    let y = 16;

    // ── Header
    pdf.setTextColor(0, 0, 0);
    if (nombre) {
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(20);
      pdf.text(nombre, pageW / 2, y, { align: "center" });
      y += 8;
    }
    if (contactLine.length) {
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(9.5);
      const txt = contactLine.map(([l, v]) => (l && l !== "Portafolio") ? `${l}: ${v}` : v).join(" | ");
      pdf.text(txt, pageW / 2, y, { align: "center", maxWidth: usable });
      y += 5;
    }
    // Línea separadora
    pdf.setLineWidth(0.4);
    pdf.line(left, y + 1, right, y + 1);
    y += 6;

    // ── Helpers
    function sectionTitle(title) {
      if (y > pageH - 30) { pdf.addPage(); y = 20; }
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(10);
      pdf.setTextColor(0, 0, 0);
      pdf.text(title.toUpperCase(), left, y);
      y += 1.5;
      pdf.setLineWidth(0.2);
      pdf.line(left, y, right, y);
      y += 4;
    }
    function writeLine(text, size = 10, bold = false, indent = 0) {
      if (!text) return;
      if (y > pageH - 12) { pdf.addPage(); y = 20; }
      pdf.setFont("helvetica", bold ? "bold" : "normal");
      pdf.setFontSize(size);
      pdf.setTextColor(0, 0, 0);
      const lines = pdf.splitTextToSize(String(text), usable - indent);
      for (const line of lines) {
        if (y > pageH - 10) { pdf.addPage(); y = 20; }
        pdf.text(line, left + indent, y);
        y += size * 0.42;
      }
      y += 1;
    }
    function entryHead(leftText, rightText, bold = true) {
      if (!leftText && !rightText) return;
      if (y > pageH - 14) { pdf.addPage(); y = 20; }
      const size = 10.5;
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(size);
      pdf.setTextColor(0, 0, 0);
      const startY = y;
      if (rightText) {
        const rightW = Math.max(35, usable * 0.32);
        const leftW = usable - rightW - 4;
        // left first
        const leftLines = pdf.splitTextToSize(String(leftText), leftW);
        for (const ln of leftLines) {
          if (y > pageH - 10) { pdf.addPage(); y = 20; }
          pdf.text(ln, left, y);
          y += size * 0.42;
        }
        const yAfterLeft = y;
        // right column from startY
        pdf.setFont("helvetica", "normal");
        pdf.setFontSize(9.5);
        const rightLines = pdf.splitTextToSize(String(rightText), rightW);
        let yRight = startY;
        for (const ln of rightLines) {
          if (yRight > pageH - 10) { /* page break no, it's same column */ }
          pdf.text(ln, right, yRight, { align: "right" });
          yRight += 9.5 * 0.42;
        }
        y = Math.max(yAfterLeft, yRight) + 1.5;
      } else {
        writeLine(leftText, size, bold);
      }
    }
    function bullet(text) {
      writeLine("• " + text, 10, false, 3);
    }

    // ── Profile
    const resumen = (data.perfil_profesional && data.perfil_profesional.resumen || "").trim();
    if (resumen) {
      sectionTitle("Perfil Profesional");
      writeLine(resumen, 10, false);
      y += 2;
    }

    // ── Experience
    if (Array.isArray(data.experiencia) && data.experiencia.length) {
      sectionTitle("Experiencia");
      for (const item of data.experiencia) {
        if (!item || typeof item !== "object") { writeLine(String(item), 10); continue; }
        const title = [item.cargo, item.empresa].filter(Boolean).join(", ");
        const drange = CvRender._fmtDateRange(item);
        entryHead(title, drange, true);
        const loc = (item.ubicacion || "").trim();
        if (loc) writeLine(loc, 9.5, false);
        for (const key of ["responsabilidades", "logros"]) {
          const v = item[key];
          if (!v) continue;
          const rows = Array.isArray(v) ? v : String(v).split("\n").map((s) => s.trim()).filter(Boolean);
          for (const r of rows) bullet(r);
        }
        y += 2;
      }
    }

    // ── Skills
    const hab = data.habilidades || {};
    const tech = (typeof CvRender._mergeTecnicas === "function")
      ? CvRender._mergeTecnicas(hab.tecnicas, (data.perfil_profesional || {}).palabras_clave)
      : (hab.tecnicas || []);
    const soft = hab.blandas || [];
    const langs = hab.idiomas || [];
    if (tech.length || soft.length || langs.length) {
      sectionTitle("Habilidades");
      if (tech.length) writeLine("Técnicas: " + tech.join(", "), 10);
      if (soft.length) writeLine("Habilidades Blandas: " + soft.join(", "), 10);
      if (langs.length) writeLine("Idiomas: " + langs.join(", "), 10);
      y += 2;
    }

    // ── Education & Certifications
    const edu = data.educacion || [];
    const certs = data.certificaciones || [];
    if (edu.length || certs.length) {
      sectionTitle("Educación y Certificaciones");
      for (const item of edu) {
        if (!item || typeof item !== "object") { writeLine(String(item), 10); continue; }
        const leftText = [item.institucion, item.titulo].filter(Boolean).join(" — ");
        const dr = [];
        if (item.fecha_inicio || item.fecha_fin) {
          dr.push([item.fecha_inicio || "", item.fecha_fin || "Present"].filter(Boolean).map(CvRender._fmtDateShort).join(" – "));
        }
        if (item.estado) dr.push(String(item.estado));
        const rightText = dr.join(" · ");
        entryHead(leftText, rightText, false);
        if (item.ubicacion) writeLine(String(item.ubicacion).trim(), 9.5, false);
        y += 1.5;
      }
      for (const c of certs) {
        if (!c || typeof c !== "object") { writeLine(String(c), 10); continue; }
        const name = (c.nombre || c.titulo || "").trim();
        const desc = (c.descripcion || c.detalle || "").trim();
        if (name && desc) writeLine(`${name} — ${desc}`, 10);
        else if (name) writeLine(name, 10);
        else if (desc) writeLine(desc, 10);
        y += 1;
      }
      y += 1;
    }

    // ── Projects
    if (Array.isArray(data.proyectos) && data.proyectos.length) {
      sectionTitle("Proyectos");
      for (const item of data.proyectos) {
        if (!item || typeof item !== "object") { writeLine(String(item), 10); continue; }
        if (item.nombre) writeLine(String(item.nombre).trim(), 11.5, true);
        if (item.descripcion) writeLine(String(item.descripcion), 10);
        if (Array.isArray(item.tecnologias) && item.tecnologias.length) {
          writeLine("Tecnologías: " + item.tecnologias.join(", "), 9.5);
        }
        if (item.enlace) writeLine("Enlace: " + _clean(String(item.enlace).trim()), 9.5);
        y += 2;
      }
    }

    // ── Additional
    const strengths = data.fortalezas || [];
    if (Array.isArray(strengths) && strengths.length) {
      const rows = [];
      for (const s of strengths) {
        if (!s || typeof s !== "object") { const v = String(s || "").trim(); if (v) rows.push(v); continue; }
        const st = (s.titulo || s.nombre || "").trim();
        const sd = (s.descripcion || "").trim();
        if (st && sd) rows.push(`${st}: ${sd}`);
        else if (st) rows.push(st);
        else if (sd) rows.push(sd);
      }
      if (rows.length) {
        sectionTitle("Adicional");
        for (const r of rows) bullet(r);
      }
    }

    return pdf;
  }

  // Reuso de CvRender._contactLine si está, sino calculo local
  function _contactLineLocal(meta, data) {
    const raw = meta && meta.contacto;
    if (!raw || typeof raw !== "object") return [];
    const order = [["Teléfono","telefono"],["Email","email"],["LinkedIn","linkedin"],["Ubicación","ubicacion"]];
    const out = [];
    for (const [label, key] of order) {
      const v = raw[key];
      if (v == null) continue;
      const s = String(v).trim();
      if (s) out.push([label, s]);
    }
    return out;
  }

  return { build };
})();

window.PdfGenerator = PdfGenerator;
