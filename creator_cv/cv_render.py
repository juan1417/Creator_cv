from __future__ import annotations

import html
import io
import json
import os
import platform
import re
from pathlib import Path
from typing import Any

import markdown as md_lib
from docx import Document
from fpdf import FPDF


def markdown_to_preview_html(md: str) -> str:
    """HTML seguro para vista previa en navegador (Markdown → HTML)."""
    return md_lib.markdown(
        md,
        extensions=["extra", "nl2br", "sane_lists"],
    )


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _normalize_link_list(links: Any) -> list[str]:
    """Lista de enlaces o un solo string con URLs separadas por comas."""
    if links is None:
        return []
    if isinstance(links, list):
        return [str(x).strip() for x in links if str(x).strip()]
    if isinstance(links, str):
        s = links.strip()
        if not s:
            return []
        return [p.strip() for p in s.split(",") if p.strip()]
    return []


def _contact_line(meta: dict[str, Any]) -> list[tuple[str, str]]:
    """Pares (etiqueta, valor) para la cabecera; solo entradas con texto."""
    raw = meta.get("contacto")
    if not isinstance(raw, dict):
        return []
    order = (
        ("Teléfono", "telefono"),
        ("Email", "email"),
        ("LinkedIn", "linkedin"),
        ("Ubicación", "ubicacion"),
    )
    out: list[tuple[str, str]] = []
    for label, key in order:
        val = raw.get(key)
        if val is None:
            continue
        s = str(val).strip()
        if s:
            out.append((label, s))
    return out


def _meta_contact_nonempty(meta: dict[str, Any]) -> bool:
    return bool(_contact_line(meta))


def _merge_tecnicas_lists(
    explicit: Any,
    from_keywords: Any,
) -> list[str]:
    """
    Lista única para mostrar/exportar: habilidades.tecnicas primero, luego
    perfil_profesional.palabras_clave que no estén ya (mismo uso práctico que stack).
    """
    out: list[str] = []
    seen: set[str] = set()

    def _add_many(raw: Any) -> None:
        if raw is None:
            return
        items = raw if isinstance(raw, list) else [raw]
        for x in items:
            s = str(x).strip()
            if not s:
                continue
            key = s.casefold()
            if key not in seen:
                seen.add(key)
                out.append(s)

    _add_many(explicit)
    _add_many(from_keywords)
    return out


def context_has_preview_content(data: dict[str, Any]) -> bool:
    """True si la vista previa estructurada tendría bloques de CV visibles."""
    meta = data.get("meta") or {}
    if str(meta.get("nombre_completo") or "").strip():
        return True
    if str(meta.get("titulo_profesional") or "").strip():
        return True
    if str(meta.get("objetivo_cv") or "").strip():
        return True
    if _meta_contact_nonempty(meta):
        return True
    perfil = data.get("perfil_profesional") or {}
    if (perfil.get("resumen") or "").strip():
        return True
    if perfil.get("palabras_clave"):
        return True
    if data.get("experiencia"):
        return True
    if data.get("educacion"):
        return True
    hab = data.get("habilidades") or {}
    if hab.get("tecnicas") or hab.get("blandas") or hab.get("idiomas"):
        return True
    if data.get("proyectos"):
        return True
    if data.get("certificaciones"):
        return True
    if data.get("fortalezas"):
        return True
    return False


def _exp_date_range(item: dict[str, Any]) -> str:
    fin = item.get("fecha_fin") or ("actual" if item.get("actual") else "")
    parts = [x for x in (item.get("fecha_inicio") or "", fin) if x]
    return " – ".join(parts)


def context_to_structured_preview_html(
    data: dict[str, Any],
    *,
    fallback_title: str = "",
) -> str:
    """
    HTML semántico para vista previa (diseño dos columnas, estilo CV moderno).
    Todo el texto de usuario pasa por escape HTML.
    """
    parts: list[str] = []
    meta = data.get("meta") or {}
    nombre = (meta.get("nombre_completo") or "").strip()
    if not nombre and fallback_title:
        nombre = fallback_title.strip()
    subtitle = (meta.get("titulo_profesional") or "").strip() or (
        meta.get("objetivo_cv") or ""
    ).strip()

    parts.append('<article class="cv-ref">')
    parts.append('<header class="cv-ref__header">')
    if nombre:
        parts.append(f'<h1 class="cv-ref__name">{_e(nombre.upper())}</h1>')
    if subtitle:
        parts.append(f'<p class="cv-ref__subtitle">{_e(subtitle)}</p>')
    contact = _contact_line(meta)
    if contact:
        parts.append('<ul class="cv-ref__contact" role="list">')
        for label, val in contact:
            parts.append(
                '<li>'
                f'<span class="cv-ref__contact-label">{_e(label)}</span> '
                f'<span class="cv-ref__contact-val">{_e(val)}</span>'
                "</li>"
            )
        parts.append("</ul>")
    parts.append("</header>")

    aside_parts: list[str] = []
    certs = data.get("certificaciones") or []
    if isinstance(certs, list) and certs:
        cert_body: list[str] = []
        for c in certs:
            if not isinstance(c, dict):
                cert_body.append(f'<p class="cv-ref__cert-line">{_e(c)}</p>')
                continue
            name = (c.get("nombre") or c.get("titulo") or "").strip()
            desc = (c.get("descripcion") or c.get("detalle") or "").strip()
            if name:
                cert_body.append(f'<h3 class="cv-ref__cert-name">{_e(name)}</h3>')
            if desc:
                cert_body.append(f'<p class="cv-ref__cert-desc">{_e(desc)}</p>')
        if cert_body:
            aside_parts.append('<section class="cv-ref__section">')
            aside_parts.append('<h2 class="cv-ref__section-title">Certificación</h2>')
            aside_parts.extend(cert_body)
            aside_parts.append("</section>")

    strengths = data.get("fortalezas") or []
    if isinstance(strengths, list) and strengths:
        str_body: list[str] = []
        for s in strengths:
            if not isinstance(s, dict):
                str_body.append(f'<p class="cv-ref__str-item">{_e(s)}</p>')
                continue
            st = (s.get("titulo") or s.get("nombre") or "").strip()
            sd = (s.get("descripcion") or "").strip()
            if not st and not sd:
                continue
            str_body.append('<div class="cv-ref__str">')
            str_body.append('<span class="cv-ref__str-marker" aria-hidden="true"></span>')
            str_body.append('<div class="cv-ref__str-text">')
            if st:
                str_body.append(f'<strong class="cv-ref__str-title">{_e(st)}</strong>')
            if sd:
                str_body.append(f'<p class="cv-ref__str-desc">{_e(sd)}</p>')
            str_body.append("</div></div>")
        if str_body:
            aside_parts.append('<section class="cv-ref__section">')
            aside_parts.append('<h2 class="cv-ref__section-title">Fortalezas</h2>')
            aside_parts.extend(str_body)
            aside_parts.append("</section>")

    hab = data.get("habilidades") or {}
    perfil_kw = (data.get("perfil_profesional") or {}).get("palabras_clave") or []
    tech = _merge_tecnicas_lists(hab.get("tecnicas"), perfil_kw)
    soft = hab.get("blandas") or []
    langs = hab.get("idiomas") or []
    if tech or soft or langs:
        aside_parts.append('<section class="cv-ref__section">')
        aside_parts.append('<h2 class="cv-ref__section-title">Habilidades</h2>')
        if tech:
            aside_parts.append('<p class="cv-ref__skills-sub">Técnicas</p>')
            aside_parts.append('<div class="cv-ref__pills">')
            for t in tech:
                aside_parts.append(f'<span class="cv-ref__pill">{_e(t)}</span>')
            aside_parts.append("</div>")
        if soft:
            aside_parts.append('<p class="cv-ref__skills-sub">Blandas</p>')
            aside_parts.append('<ul class="cv-ref__list cv-ref__list--plain">')
            for item in soft:
                aside_parts.append(f"<li>{_e(item)}</li>")
            aside_parts.append("</ul>")
        if langs:
            aside_parts.append('<p class="cv-ref__skills-sub">Idiomas</p>')
            aside_parts.append('<ul class="cv-ref__list cv-ref__list--muted">')
            for item in langs:
                aside_parts.append(f"<li>{_e(item)}</li>")
            aside_parts.append("</ul>")
        aside_parts.append("</section>")

    aside_html = "".join(aside_parts)
    grid_class = (
        "cv-ref__grid cv-ref__grid--single"
        if not aside_html
        else "cv-ref__grid"
    )
    parts.append(f'<div class="{grid_class}">')
    if aside_html:
        parts.append(
            '<aside class="cv-ref__aside" aria-label="Certificaciones y habilidades">'
        )
        parts.append(aside_html)
        parts.append("</aside>")

    parts.append('<div class="cv-ref__main">')

    perfil = data.get("perfil_profesional") or {}
    resumen = (perfil.get("resumen") or "").strip()
    if resumen:
        parts.append('<section class="cv-ref__section">')
        parts.append('<h2 class="cv-ref__section-title">Perfil profesional</h2>')
        parts.append(f'<p class="cv-ref__para">{_e(resumen)}</p>')
        parts.append("</section>")

    exp = data.get("experiencia") or []
    if isinstance(exp, list) and exp:
        parts.append('<section class="cv-ref__section">')
        parts.append('<h2 class="cv-ref__section-title">Experiencia</h2>')
        for item in exp:
            if not isinstance(item, dict):
                parts.append(f'<p class="cv-ref__para">{_e(item)}</p>')
                continue
            cargo = (item.get("cargo") or "").strip()
            org = (item.get("empresa") or "").strip()
            loc = (item.get("ubicacion") or "").strip()
            drange = _exp_date_range(item)
            parts.append('<div class="cv-ref__timeline-item">')
            parts.append('<div class="cv-ref__job-head">')
            parts.append('<div class="cv-ref__job-titles">')
            if cargo:
                parts.append(f'<div class="cv-ref__role">{_e(cargo)}</div>')
            if org:
                parts.append(f'<div class="cv-ref__org">{_e(org)}</div>')
            parts.append("</div>")
            parts.append('<div class="cv-ref__job-meta">')
            if drange:
                parts.append(
                    f'<span class="cv-ref__meta cv-ref__meta--date">{_e(drange)}</span>'
                )
            if loc:
                parts.append(
                    f'<span class="cv-ref__meta cv-ref__meta--loc">{_e(loc)}</span>'
                )
            parts.append("</div></div>")
            for label, key in (
                ("Responsabilidades", "responsabilidades"),
                ("Logros", "logros"),
            ):
                val = item.get(key)
                if not val:
                    continue
                parts.append(f'<p class="cv-ref__label">{_e(label)}</p>')
                if isinstance(val, list):
                    parts.append('<ul class="cv-ref__list">')
                    for row in val:
                        parts.append(f"<li>{_e(row)}</li>")
                    parts.append("</ul>")
                else:
                    parts.append(f'<p class="cv-ref__para">{_e(val)}</p>')
            parts.append("</div>")
        parts.append("</section>")

    edu = data.get("educacion") or []
    if isinstance(edu, list) and edu:
        parts.append('<section class="cv-ref__section">')
        parts.append('<h2 class="cv-ref__section-title">Educación</h2>')
        for item in edu:
            if not isinstance(item, dict):
                parts.append(f'<p class="cv-ref__para">{_e(item)}</p>')
                continue
            titulo = (item.get("titulo") or "").strip()
            inst = (item.get("institucion") or "").strip()
            loc = (item.get("ubicacion") or "").strip()
            extra: list[str] = []
            if item.get("fecha_inicio") or item.get("fecha_fin"):
                extra.append(
                    " – ".join(
                        x
                        for x in (
                            item.get("fecha_inicio") or "",
                            item.get("fecha_fin") or "",
                        )
                        if x
                    )
                )
            if item.get("estado"):
                extra.append(str(item["estado"]))
            parts.append('<div class="cv-ref__edu-item">')
            parts.append('<div class="cv-ref__job-head">')
            parts.append('<div class="cv-ref__job-titles">')
            if titulo:
                parts.append(f'<div class="cv-ref__role">{_e(titulo)}</div>')
            if inst:
                parts.append(f'<div class="cv-ref__org">{_e(inst)}</div>')
            parts.append("</div>")
            parts.append('<div class="cv-ref__job-meta">')
            if extra:
                parts.append(
                    f'<span class="cv-ref__meta cv-ref__meta--date">{_e("; ".join(extra))}</span>'
                )
            if loc:
                parts.append(
                    f'<span class="cv-ref__meta cv-ref__meta--loc">{_e(loc)}</span>'
                )
            parts.append("</div></div></div>")
        parts.append("</section>")

    proy = data.get("proyectos") or []
    if isinstance(proy, list) and proy:
        parts.append('<section class="cv-ref__section">')
        parts.append('<h2 class="cv-ref__section-title">Proyectos</h2>')
        for item in proy:
            if not isinstance(item, dict):
                parts.append(f'<p class="cv-ref__para">{_e(item)}</p>')
                continue
            name = (item.get("nombre") or "Proyecto").strip()
            parts.append("<div>")
            parts.append(f'<h3 class="cv-ref__proj-name">{_e(name)}</h3>')
            if item.get("descripcion"):
                parts.append(
                    f'<p class="cv-ref__para">{_e(item["descripcion"])}</p>'
                )
            if item.get("tecnologias"):
                tec = item["tecnologias"]
                if isinstance(tec, list):
                    parts.append(
                        '<p class="cv-ref__keywords"><strong>Tecnologías:</strong> '
                        f'{_e(", ".join(str(x) for x in tec))}</p>'
                    )
            if item.get("enlace"):
                parts.append(
                    f'<p class="cv-ref__link"><strong>Enlace:</strong> {_e(item["enlace"])}</p>'
                )
            parts.append("</div>")
        parts.append("</section>")

    parts.append("</div></div></article>")
    return "".join(parts)


def _fmt_val(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "sí" if v else "no"
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def json_to_markdown(data: dict[str, Any]) -> str:
    """Solo formatea el JSON ya guardado; no inventa contenido."""
    lines: list[str] = []

    meta = data.get("meta") or {}
    if any(meta.values()):
        lines.append("## Meta")
        for key in (
            "nombre_completo",
            "titulo_profesional",
            "idioma_cv",
            "objetivo_cv",
            "tipo_cv",
            "nivel_seniority",
        ):
            val = meta.get(key)
            if val:
                lines.append(f"- **{key}**: {val}")
        contact = meta.get("contacto")
        if isinstance(contact, dict):
            for ck, label in (
                ("telefono", "Teléfono"),
                ("email", "Email"),
                ("linkedin", "LinkedIn"),
                ("ubicacion", "Ubicación"),
            ):
                cv = contact.get(ck)
                if cv and str(cv).strip():
                    lines.append(f"- **{label}**: {cv}")
        lines.append("")

    certs = data.get("certificaciones") or []
    if isinstance(certs, list) and certs:
        lines.append("## Certificaciones")
        for c in certs:
            if not isinstance(c, dict):
                lines.append(f"- {_fmt_val(c)}")
                continue
            name = (c.get("nombre") or c.get("titulo") or "").strip()
            desc = (c.get("descripcion") or c.get("detalle") or "").strip()
            if name and desc:
                lines.append(f"- **{name}**: {desc}")
            elif name:
                lines.append(f"- **{name}**")
            elif desc:
                lines.append(f"- {desc}")
        lines.append("")

    strengths = data.get("fortalezas") or []
    if isinstance(strengths, list) and strengths:
        lines.append("## Fortalezas")
        for s in strengths:
            if not isinstance(s, dict):
                lines.append(f"- {_fmt_val(s)}")
                continue
            st = (s.get("titulo") or s.get("nombre") or "").strip()
            sd = (s.get("descripcion") or "").strip()
            if st and sd:
                lines.append(f"- **{st}**: {sd}")
            elif st:
                lines.append(f"- **{st}**")
            elif sd:
                lines.append(f"- {sd}")
        lines.append("")

    perfil = data.get("perfil_profesional") or {}
    resumen = (perfil.get("resumen") or "").strip()
    if resumen:
        lines.append("## Perfil profesional")
        lines.append(resumen)
        lines.append("")

    exp = data.get("experiencia") or []
    if exp:
        lines.append("## Experiencia")
        for item in exp:
            if not isinstance(item, dict):
                lines.append(f"- {_fmt_val(item)}")
                continue
            title = item.get("cargo") or ""
            org = item.get("empresa") or ""
            head = " · ".join(x for x in (title, org) if x)
            if head:
                lines.append(f"### {head}")
            dates = " – ".join(
                x
                for x in (
                    item.get("fecha_inicio") or "",
                    item.get("fecha_fin") or ("actual" if item.get("actual") else ""),
                )
                if x
            )
            if dates:
                lines.append(dates)
            for label, key in (
                ("Ubicación", "ubicacion"),
                ("Responsabilidades", "responsabilidades"),
                ("Logros", "logros"),
            ):
                val = item.get(key)
                if not val:
                    continue
                if isinstance(val, list):
                    lines.append(f"**{label}:**")
                    for row in val:
                        lines.append(f"- {row}")
                else:
                    lines.append(f"**{label}:** {val}")
            lines.append("")

    edu = data.get("educacion") or []
    if edu:
        lines.append("## Educación")
        for item in edu:
            if not isinstance(item, dict):
                lines.append(f"- {_fmt_val(item)}")
                continue
            t = item.get("titulo") or ""
            inst = item.get("institucion") or ""
            head = " · ".join(x for x in (t, inst) if x)
            line = f"- {head}" if head else f"- {_fmt_val(item)}"
            extra = []
            if item.get("fecha_inicio") or item.get("fecha_fin"):
                extra.append(
                    " – ".join(
                        x
                        for x in (
                            item.get("fecha_inicio") or "",
                            item.get("fecha_fin") or "",
                        )
                        if x
                    )
                )
            if item.get("estado"):
                extra.append(str(item["estado"]))
            if extra:
                line += " (" + "; ".join(extra) + ")"
            lines.append(line)
        lines.append("")

    hab = data.get("habilidades") or {}
    if hab:
        perfil_kw = (data.get("perfil_profesional") or {}).get("palabras_clave") or []
        tech = _merge_tecnicas_lists(hab.get("tecnicas"), perfil_kw)
        soft = hab.get("blandas") or []
        langs = hab.get("idiomas") or []
        if tech or soft or langs:
            lines.append("## Habilidades")
            if tech:
                lines.append("**Técnicas:** " + ", ".join(str(x) for x in tech))
            if soft:
                lines.append("**Blandas:** " + ", ".join(str(x) for x in soft))
            if langs:
                lines.append("**Idiomas:** " + ", ".join(str(x) for x in langs))
            lines.append("")

    proy = data.get("proyectos") or []
    if proy:
        lines.append("## Proyectos")
        for item in proy:
            if not isinstance(item, dict):
                lines.append(f"- {_fmt_val(item)}")
                continue
            name = item.get("nombre") or "Proyecto"
            lines.append(f"### {name}")
            if item.get("descripcion"):
                lines.append(str(item["descripcion"]))
            if item.get("tecnologias"):
                tec = item["tecnologias"]
                if isinstance(tec, list):
                    lines.append("**Tecnologías:** " + ", ".join(str(x) for x in tec))
            if item.get("enlace"):
                lines.append(f"**Enlace:** {item['enlace']}")
            lines.append("")

    rec = data.get("recursos_actuales") or {}
    if any(rec.values()):
        lines.append("## Recursos actuales")
        lines.append(f"- **cv_existente:** {_fmt_val(rec.get('cv_existente'))}")
        if rec.get("texto_cv"):
            lines.append("**Texto CV:**")
            lines.append(str(rec["texto_cv"]))
        links = _normalize_link_list(rec.get("links"))
        if links:
            lines.append("**Enlaces:**")
            for link in links:
                lines.append(f"- {link}")
        lines.append("")

    rest = data.get("restricciones") or {}
    if any(v not in (None, "") for v in rest.values()):
        lines.append("## Restricciones")
        for key in (
            "extension_maxima_paginas",
            "formato_solicitado",
            "otro",
        ):
            val = rest.get(key)
            if val:
                lines.append(f"- **{key}:** {val}")
        lines.append("")

    dudas = data.get("dudas_pendientes") or []
    if dudas:
        lines.append("## Dudas pendientes")
        for d in dudas:
            lines.append(f"- {d}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def markdown_to_docx_bytes(md: str) -> bytes:
    doc = Document()
    for line in md.split("\n"):
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith(("- ", "* ")):
            doc.add_paragraph(line[2:].strip(), style="List Bullet")
        else:
            doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _unicode_font_path() -> Path | None:
    """TTF con soporte Unicode (Windows / Linux / macOS)."""
    system = platform.system()
    candidates: list[Path] = []
    if system == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        candidates = [
            Path(windir) / "Fonts" / "arial.ttf",
            Path(windir) / "Fonts" / "calibri.ttf",
            Path(windir) / "Fonts" / "segoeui.ttf",
        ]
    elif system == "Darwin":
        candidates = [
            Path("/Library/Fonts/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        ]
    else:
        candidates = [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _strip_inline_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    return text


def _fold_latin_fallback(text: str) -> str:
    """Último recurso si no hay TTF: aproximar a Latin-1."""
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u202f", " ")
        .replace("\u00a0", " ")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )


def markdown_to_pdf_bytes(md: str) -> bytes:
    """
    PDF desde Markdown. Usa una fuente TrueType del sistema para Unicode;
    sin fuente disponible, simplifica caracteres para Helvetica.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()
    page_w = pdf.epw

    font_path = _unicode_font_path()
    font_family = "Helvetica"
    size_body = 10
    size_h1, size_h2, size_h3 = 16, 13, 11
    line_h = 5

    if font_path:
        pdf.add_font("CvBody", "", str(font_path))
        font_family = "CvBody"
        pdf.set_font("CvBody", size=size_body)
    else:
        md = _fold_latin_fallback(md)
        pdf.set_font("Helvetica", size=size_body)

    def _write_line(text: str, height: float) -> None:
        # En fpdf2, fijamos explícitamente el salto para evitar drift horizontal.
        pdf.multi_cell(
            page_w,
            height,
            text,
            new_x="LMARGIN",
            new_y="NEXT",
        )

    for raw in md.split("\n"):
        line = _strip_inline_markdown(raw.rstrip())
        if not line:
            pdf.set_x(pdf.l_margin)
            pdf.ln(line_h * 0.35)
            continue
        if font_path:
            pdf.set_font(font_family, size=size_body)
        else:
            pdf.set_font("Helvetica", size=size_body)

        if line.startswith("### "):
            pdf.set_font(font_family if font_path else "Helvetica", size=size_h3)
            _write_line(line[4:], line_h + 1)
        elif line.startswith("## "):
            pdf.set_font(font_family if font_path else "Helvetica", size=size_h2)
            _write_line(line[3:], line_h + 1)
        elif line.startswith("# "):
            pdf.set_font(font_family if font_path else "Helvetica", size=size_h1)
            _write_line(line[2:], line_h + 1)
        elif line.startswith(("- ", "* ")):
            if font_path:
                pdf.set_font(font_family, size=size_body)
            else:
                pdf.set_font("Helvetica", size=size_body)
            _write_line(f"  - {line[2:]}", line_h)
        else:
            if font_path:
                pdf.set_font(font_family, size=size_body)
            else:
                pdf.set_font("Helvetica", size=size_body)
            _write_line(line, line_h)

    return bytes(pdf.output())
