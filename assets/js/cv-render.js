// Renderizado de un CV a HTML/MD con la plantilla Harvard de una sola columna.
// Equivalente JS de creator_cv.cv_render (sin dependencias de servidor).

const CvRender = (() => {
  function _e(v) {
    return Shared.escapeHtml(v == null ? "" : v);
  }

  function _fmtDateShort(value) {
    if (!value) return "";
    const s = String(value).trim();
    const parts = s.split("-");
    const months = { "01":"Ene","02":"Feb","03":"Mar","04":"Abr","05":"May","06":"Jun","07":"Jul","08":"Ago","09":"Sep","10":"Oct","11":"Nov","12":"Dic" };
    if (parts.length >= 2 && months[parts[1]]) return `${months[parts[1]]} ${parts[0]}`;
    return s;
  }

  function _fmtDateRange(item) {
    const fin = item.fecha_fin || (item.actual ? "Present" : "");
    const parts = [_fmtDateShort(item.fecha_inicio || ""), _fmtDateShort(fin)].filter(Boolean);
    return parts.join(" – ");
  }

  function _cleanUrl(url) {
    if (!url) return "";
    const u = String(url).trim();
    if (u.includes("://")) return u;
    if (u.startsWith("//")) return "https:" + u;
    return "https://" + u;
  }

  function _cleanUrlForCompare(url) {
    if (!url) return "";
    let u = String(url).trim().toLowerCase();
    for (const p of ["https://", "http://", "www."]) {
      if (u.startsWith(p)) u = u.slice(p.length);
    }
    return u.replace(/\/$/, "");
  }

  function _normalizeLinkList(links) {
    if (links == null) return [];
    if (Array.isArray(links)) {
      const out = [];
      for (const x of links) {
        const s = String(x || "").trim();
        if (!s) continue;
        for (const part of s.split(",")) {
          const p = part.trim();
          if (p) out.push(p);
        }
      }
      return out;
    }
    if (typeof links === "string") {
      return links.split(",").map((p) => p.trim()).filter(Boolean);
    }
    return [];
  }

  function _contactLine(meta, data) {
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
    if (data) {
      const rec = data.recursos_actuales || {};
      const links = _normalizeLinkList(rec.links);
      if (links.length) {
        const li = (raw.linkedin || "").trim();
        const liClean = _cleanUrlForCompare(li);
        for (const link of links) {
          const stripped = String(link || "").trim();
          if (!stripped) continue;
          if (_cleanUrlForCompare(stripped) === liClean) continue;
          out.push(["Portafolio", stripped]);
        }
      }
    }
    return out;
  }

  function _mergeTecnicas(explicit, fromKeywords) {
    const out = [];
    const seen = new Set();
    function add(raw) {
      if (raw == null) return;
      const items = Array.isArray(raw) ? raw : [raw];
      for (const x of items) {
        const s = String(x).trim();
        if (!s) continue;
        const k = s.toLowerCase();
        if (!seen.has(k)) { seen.add(k); out.push(s); }
      }
    }
    add(explicit);
    add(fromKeywords);
    return out;
  }

  // ───── MD ─────
  function toMarkdown(data) {
    const lines = [];
    const meta = data.meta || {};
    if (Object.values(meta).some(Boolean)) {
      lines.push("## Meta");
      for (const k of ["nombre_completo","titulo_profesional","idioma_cv","objetivo_cv","tipo_cv","nivel_seniority"]) {
        const v = meta[k];
        if (v) lines.push(`- **${k}**: ${v}`);
      }
      const c = meta.contacto;
      if (c && typeof c === "object") {
        const parts = [];
        for (const ck of ["telefono","email","linkedin","ubicacion"]) {
          if (c[ck] && String(c[ck]).trim()) parts.push(String(c[ck]).trim());
        }
        const rec = data.recursos_actuales || {};
        const li = (c.linkedin || "").trim();
        for (const link of _normalizeLinkList(rec.links)) {
          const stripped = String(link).trim();
          if (stripped && _cleanUrlForCompare(stripped) !== _cleanUrlForCompare(li)) parts.push(stripped);
        }
        if (parts.length) lines.push("- " + parts.join(" | "));
      }
      lines.push("");
    }

    const resumen = (data.perfil_profesional && data.perfil_profesional.resumen || "").trim();
    if (resumen) {
      lines.push("## Perfil Profesional");
      lines.push(resumen);
      lines.push("");
    }

    if (Array.isArray(data.experiencia) && data.experiencia.length) {
      lines.push("## Experiencia");
      for (const item of data.experiencia) {
        if (!item || typeof item !== "object") { lines.push(`- ${item}`); continue; }
        const head = [item.cargo, item.empresa].filter(Boolean).join(", ");
        if (head) lines.push(`### ${head}`);
        const drange = [item.fecha_inicio, item.fecha_fin || (item.actual ? "Present" : "")]
          .filter(Boolean).map(_fmtDateShort).join(" – ");
        if (drange) lines.push(drange);
        for (const [label, key] of [["Ubicación","ubicacion"],["Responsabilidades","responsabilidades"],["Logros","logros"]]) {
          const v = item[key];
          if (!v) continue;
          if (Array.isArray(v)) {
            lines.push(`**${label}:**`);
            for (const r of v) lines.push(`- ${r}`);
          } else {
            lines.push(`**${label}:** ${v}`);
          }
        }
        lines.push("");
      }
    }

    const hab = data.habilidades || {};
    if (hab) {
      const tech = _mergeTecnicas(hab.tecnicas, (data.perfil_profesional || {}).palabras_clave);
      const soft = hab.blandas || [];
      const langs = hab.idiomas || [];
      if (tech.length || soft.length || langs.length) {
        lines.push("## Habilidades");
        if (tech.length) lines.push("**Técnicas:** " + tech.join(", "));
        if (soft.length) lines.push("**Habilidades Blandas:** " + soft.join(", "));
        if (langs.length) lines.push("**Idiomas:** " + langs.join(", "));
        lines.push("");
      }
    }

    const edu = data.educacion || [];
    const certs = data.certificaciones || [];
    if (edu.length || certs.length) {
      lines.push("## Educación y Certificaciones");
      for (const item of edu) {
        if (!item || typeof item !== "object") { lines.push(`- ${item}`); continue; }
        const head = [item.institucion, item.titulo].filter(Boolean).join(" — ");
        let line = head ? `- ${head}` : `- ${JSON.stringify(item)}`;
        const extra = [];
        if (item.fecha_inicio || item.fecha_fin) {
          extra.push([_fmtDateShort(item.fecha_inicio || ""), _fmtDateShort(item.fecha_fin || "Present")].filter(Boolean).join(" – "));
        }
        if (item.estado) extra.push(String(item.estado));
        if (extra.length) line += " (" + extra.join("; ") + ")";
        lines.push(line);
      }
      for (const c of certs) {
        if (!c || typeof c !== "object") { lines.push(`- ${c}`); continue; }
        const name = (c.nombre || c.titulo || "").trim();
        const desc = (c.descripcion || c.detalle || "").trim();
        if (name && desc) lines.push(`- **${name}**: ${desc}`);
        else if (name) lines.push(`- **${name}**`);
        else if (desc) lines.push(`- ${desc}`);
      }
      lines.push("");
    }

    if (Array.isArray(data.proyectos) && data.proyectos.length) {
      lines.push("## Proyectos");
      for (const item of data.proyectos) {
        if (!item || typeof item !== "object") { lines.push(`- ${item}`); continue; }
        const name = (item.nombre || "Proyecto").trim();
        lines.push(`### ${name}`);
        if (item.descripcion) lines.push(String(item.descripcion));
        if (Array.isArray(item.tecnologias) && item.tecnologias.length) {
          lines.push("**Tecnologías:** " + item.tecnologias.join(", "));
        }
        if (item.enlace) {
          lines.push(`**Enlace:** <${_cleanUrl(String(item.enlace).trim())}>`);
        }
        lines.push("");
      }
    }

    const strengths = data.fortalezas || [];
    if (Array.isArray(strengths) && strengths.length) {
      lines.push("## Adicional");
      for (const s of strengths) {
        if (!s || typeof s !== "object") { if (s) lines.push(`- ${s}`); continue; }
        const st = (s.titulo || s.nombre || "").trim();
        const sd = (s.descripcion || "").trim();
        if (st && sd) lines.push(`- **${st}**: ${sd}`);
        else if (st) lines.push(`- **${st}**`);
        else if (sd) lines.push(`- ${sd}`);
      }
      lines.push("");
    }
    return lines.join("\n");
  }

  // ───── HTML (para preview) ─────
  function toPreviewHtml(data, fallbackTitle = "") {
    const parts = [];
    const meta = data.meta || {};
    const nombre = (meta.nombre_completo || "").trim() || fallbackTitle.trim();

    parts.push('<article class="cv-ref">');
    parts.push('<header class="cv-ref__header">');
    if (nombre) parts.push(`<h1 class="cv-ref__name">${_e(nombre)}</h1>`);
    const contact = _contactLine(meta, data);
    if (contact.length) {
      parts.push('<p class="cv-ref__contact-line">');
      for (let i = 0; i < contact.length; i++) {
        if (i > 0) parts.push('<span class="cv-ref__sep" aria-hidden="true">|</span> ');
        const [label, val] = contact[i];
        if (label === "Portafolio") {
          const url = _cleanUrl(val);
          parts.push(
            `<span class="cv-ref__contact-val">` +
            `<a href="${_e(url)}" target="_blank" rel="noopener noreferrer" class="cv-ref__proj-link-anchor">${_e(val)}</a>` +
            `</span>`
          );
        } else {
          parts.push(`<span class="cv-ref__contact-val">${_e(val)}</span>`);
        }
      }
      parts.push("</p>");
    }
    parts.push("</header>");

    const resumen = (data.perfil_profesional && data.perfil_profesional.resumen || "").trim();
    if (resumen) {
      parts.push('<section class="cv-ref__section">');
      parts.push('<h2 class="cv-ref__section-title">Perfil Profesional</h2>');
      parts.push(`<p class="cv-ref__para">${_e(resumen)}</p>`);
      parts.push("</section>");
    }

    if (Array.isArray(data.experiencia) && data.experiencia.length) {
      parts.push('<section class="cv-ref__section">');
      parts.push('<h2 class="cv-ref__section-title">Experiencia</h2>');
      for (const item of data.experiencia) {
        if (!item || typeof item !== "object") {
          parts.push(`<p class="cv-ref__entry">${_e(item)}</p>`); continue;
        }
        const cargo = (item.cargo || "").trim();
        const org = (item.empresa || "").trim();
        const loc = (item.ubicacion || "").trim();
        const drange = _fmtDateRange(item);
        parts.push('<div class="cv-ref__entry">');
        parts.push('<div class="cv-ref__entry-head">');
        parts.push('<div class="cv-ref__entry-main">');
        if (cargo) parts.push(`<span class="cv-ref__entry-role">${_e(cargo)}</span>`);
        if (org) parts.push(`<span class="cv-ref__entry-org">, ${_e(org)}</span>`);
        parts.push("</div>");
        parts.push('<div class="cv-ref__entry-aside">');
        if (drange) parts.push(`<span class="cv-ref__entry-date">${_e(drange)}</span>`);
        if (loc) parts.push(`<span class="cv-ref__entry-loc">${_e(loc)}</span>`);
        parts.push("</div></div>");
        for (const key of ["responsabilidades", "logros"]) {
          const v = item[key];
          if (!v) continue;
          const rows = Array.isArray(v) ? v : String(v).split("\n").map((s) => s.trim()).filter(Boolean);
          if (rows.length) {
            parts.push('<ul class="cv-ref__bullets">');
            for (const r of rows) parts.push(`<li>${_e(r)}</li>`);
            parts.push("</ul>");
          }
        }
        parts.push("</div>");
      }
      parts.push("</section>");
    }

    const hab = data.habilidades || {};
    const tech = _mergeTecnicas(hab.tecnicas, (data.perfil_profesional || {}).palabras_clave);
    const soft = hab.blandas || [];
    const langs = hab.idiomas || [];
    if (tech.length || soft.length || langs.length) {
      parts.push('<section class="cv-ref__section">');
      parts.push('<h2 class="cv-ref__section-title">Habilidades</h2>');
      if (tech.length) parts.push(`<p class="cv-ref__skills-row"><span class="cv-ref__skills-label">Técnicas:</span> <span class="cv-ref__skills-val">${_e(tech.join(", "))}</span></p>`);
      if (soft.length) parts.push(`<p class="cv-ref__skills-row"><span class="cv-ref__skills-label">Habilidades Blandas:</span> <span class="cv-ref__skills-val">${_e(soft.join(", "))}</span></p>`);
      if (langs.length) parts.push(`<p class="cv-ref__skills-row"><span class="cv-ref__skills-label">Idiomas:</span> <span class="cv-ref__skills-val">${_e(langs.join(", "))}</span></p>`);
      parts.push("</section>");
    }

    if (edu.length || certs.length) {
      parts.push('<section class="cv-ref__section">');
      parts.push('<h2 class="cv-ref__section-title">Educación y Certificaciones</h2>');
      for (const item of edu) {
        if (!item || typeof item !== "object") { parts.push(`<p class="cv-ref__entry">${_e(item)}</p>`); continue; }
        const titulo = (item.titulo || "").trim();
        const inst = (item.institucion || "").trim();
        const loc = (item.ubicacion || "").trim();
        const drangeParts = [];
        if (item.fecha_inicio || item.fecha_fin) {
          drangeParts.push([item.fecha_inicio || "", item.fecha_fin || "Present"].filter(Boolean).join(" – "));
        }
        if (item.estado) drangeParts.push(String(item.estado));
        const drange = drangeParts.join(" · ");
        parts.push('<div class="cv-ref__entry">');
        parts.push('<div class="cv-ref__entry-head">');
        parts.push('<div class="cv-ref__entry-main">');
        if (inst) parts.push(`<span class="cv-ref__entry-org">${_e(inst)}</span>`);
        if (titulo) {
          if (inst) parts.push(" — ");
          parts.push(`<span class="cv-ref__entry-role">${_e(titulo)}</span>`);
        }
        parts.push("</div>");
        parts.push('<div class="cv-ref__entry-aside">');
        if (drange) parts.push(`<span class="cv-ref__entry-date">${_e(drange)}</span>`);
        if (loc) parts.push(`<span class="cv-ref__entry-loc">${_e(loc)}</span>`);
        parts.push("</div></div>");
        parts.push("</div>");
      }
      for (const c of certs) {
        if (!c || typeof c !== "object") { parts.push(`<p class="cv-ref__entry">${_e(c)}</p>`); continue; }
        const name = (c.nombre || c.titulo || "").trim();
        const desc = (c.descripcion || c.detalle || "").trim();
        if (!name && !desc) continue;
        parts.push('<div class="cv-ref__entry">');
        if (name) parts.push(`<span class="cv-ref__entry-role">${_e(name)}</span>`);
        if (desc) parts.push(`<span class="cv-ref__entry-org"> — ${_e(desc)}</span>`);
        parts.push("</div>");
      }
      parts.push("</section>");
    }

    if (Array.isArray(data.proyectos) && data.proyectos.length) {
      parts.push('<section class="cv-ref__section">');
      parts.push('<h2 class="cv-ref__section-title">Proyectos</h2>');
      for (const item of data.proyectos) {
        if (!item || typeof item !== "object") { parts.push(`<p class="cv-ref__entry">${_e(item)}</p>`); continue; }
        const name = (item.nombre || "").trim();
        const desc = (item.descripcion || "").trim();
        const tec = item.tecnologias || [];
        const link = (item.enlace || "").trim();
        parts.push('<div class="cv-ref__entry">');
        if (name) parts.push(`<div class="cv-ref__proj-name">${_e(name)}</div>`);
        if (desc || tec.length || link) {
          parts.push('<div class="cv-ref__proj-meta">');
          if (desc) parts.push(`<span class="cv-ref__proj-desc">${_e(desc)}</span>`);
          if (Array.isArray(tec) && tec.length) {
            parts.push(`<span class="cv-ref__proj-tech"><span class="cv-ref__proj-tech-label">Tecnologías:</span> <span class="cv-ref__proj-tech-val">${_e(tec.join(", "))}</span></span>`);
          }
          if (link) {
            const href = _cleanUrl(link);
            parts.push(`<span class="cv-ref__proj-link"><span class="cv-ref__proj-link-label">Enlace:</span> <a class="cv-ref__proj-link-anchor" href="${_e(href)}" target="_blank" rel="noopener noreferrer">${_e(link)}</a></span>`);
          }
          parts.push("</div>");
        }
        parts.push("</div>");
      }
      parts.push("</section>");
    }

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
        parts.push('<section class="cv-ref__section">');
        parts.push('<h2 class="cv-ref__section-title">Adicional</h2>');
        parts.push('<ul class="cv-ref__bullets">');
        for (const r of rows) parts.push(`<li>${_e(r)}</li>`);
        parts.push("</ul>");
        parts.push("</section>");
      }
    }

    parts.push("</article>");
    return parts.join("");
  }

  return { toMarkdown, toPreviewHtml, _fmtDateShort, _fmtDateRange, _cleanUrl };
})();

window.CvRender = CvRender;
