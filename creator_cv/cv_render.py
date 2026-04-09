from __future__ import annotations

import asyncio
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
try:
    from fpdf.enums import XPos, YPos
except Exception:  # pragma: no cover - compatibilidad con paquetes fpdf antiguos
    XPos = None
    YPos = None


def markdown_to_preview_html(md: str) -> str:
    """HTML seguro para vista previa en navegador (Markdown → HTML)."""
    return md_lib.markdown(
        md,
        extensions=["extra", "nl2br", "sane_lists"],
    )


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _is_http_url(value: str) -> bool:
    s = value.strip().lower()
    return s.startswith("http://") or s.startswith("https://")


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
        ("Portafolio", "portafolio"),
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


def _portfolio_url(meta: dict[str, Any]) -> str:
    raw = meta.get("contacto")
    if not isinstance(raw, dict):
        return ""
    value = str(raw.get("portafolio") or "").strip()
    return value


def _collect_logros(exp: Any) -> list[str]:
    out: list[str] = []
    if not isinstance(exp, list):
        return out

    def _normalize_logro(raw: Any) -> str:
        if isinstance(raw, dict):
            # Soporta casos incorrectos donde llegó un objeto tipo proyecto.
            nombre = str(raw.get("nombre") or raw.get("titulo") or "").strip()
            desc = str(raw.get("descripcion") or raw.get("detalle") or "").strip()
            if nombre and desc:
                return f"{nombre}: {desc}"
            if desc:
                return desc
            if nombre:
                return nombre
            return ""
        s = str(raw).strip()
        return s

    for item in exp:
        if not isinstance(item, dict):
            continue
        raw = item.get("logros")
        if isinstance(raw, list):
            for row in raw:
                s = _normalize_logro(row)
                if s:
                    out.append(s)
        elif raw:
            s = _normalize_logro(raw)
            if s:
                out.append(s)
    return out


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
            safe_val = _e(val)
            if _is_http_url(val):
                rendered_val = (
                    f'<a class="cv-ref__contact-link" href="{safe_val}" '
                    'target="_blank" rel="noopener noreferrer">'
                    f"{safe_val}</a>"
                )
            else:
                rendered_val = f'<span class="cv-ref__contact-val">{safe_val}</span>'
            parts.append(
                '<li>'
                f'<span class="cv-ref__contact-label">{_e(label)}</span> '
                f"{rendered_val}"
                "</li>"
            )
        parts.append("</ul>")
    parts.append("</header>")

    aside_parts: list[str] = []
    portfolio = _portfolio_url(meta)
    if portfolio:
        aside_parts.append('<section class="cv-ref__section">')
        aside_parts.append('<h2 class="cv-ref__section-title">Portafolio</h2>')
        p = _e(portfolio)
        aside_parts.append(
            f'<p class="cv-ref__link"><a href="{p}" target="_blank" rel="noopener noreferrer">{p}</a></p>'
        )
        aside_parts.append("</section>")

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
    logros_globales = _collect_logros(exp)
    if logros_globales:
        parts.append('<section class="cv-ref__section">')
        parts.append('<h2 class="cv-ref__section-title">Logros clave</h2>')
        parts.append('<ul class="cv-ref__list">')
        for row in logros_globales:
            parts.append(f"<li>{_e(row)}</li>")
        parts.append("</ul>")
        parts.append("</section>")

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
        if portfolio:
            parts.append('<h2 class="cv-ref__section-title">Proyectos destacados</h2>')
        else:
            parts.append('<h2 class="cv-ref__section-title">Proyectos</h2>')
        for item in proy:
            if not isinstance(item, dict):
                parts.append(f'<p class="cv-ref__para">{_e(item)}</p>')
                continue
            name = (item.get("nombre") or "Proyecto").strip()
            parts.append("<div>")
            parts.append(f'<h3 class="cv-ref__proj-name">{_e(name)}</h3>')
            if item.get("descripcion") and not portfolio:
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


def context_to_preview_document_html(
    data: dict[str, Any],
    *,
    css_text: str,
    fallback_title: str = "",
) -> str:
    """Documento HTML completo para exportación fiel del preview."""
    preview_html = context_to_structured_preview_html(data, fallback_title=fallback_title)
    doc_title = _e(fallback_title or "CV")
    return (
        "<!DOCTYPE html>"
        '<html lang="es"><head><meta charset="utf-8" />'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />'
        f"<title>{doc_title}</title>"
        f"<style>{css_text}</style>"
        "<style>"
        "body{margin:0;background:#fff;color:#111827;}"
        ".preview-doc-stage{padding:0;background:transparent;border-radius:0;}"
        ".cv-paper{max-width:none;min-height:auto;box-shadow:none;border-radius:0;}"
        ".cv-paper-inner.cv-ref-doc.cv-ref-doc--pdf{padding:10mm 12mm;font-size:10pt;}"
        ".cv-ref-doc--pdf .cv-ref{break-inside:auto !important;page-break-inside:auto !important;}"
        ".cv-ref-doc--pdf .cv-ref__header{break-after:auto !important;page-break-after:auto !important;}"
        "/* Layout PDF con columnas fijas y paginacion estable */"
        ".cv-ref-doc--pdf .cv-ref__grid{display:table !important;width:100% !important;table-layout:fixed !important;}"
        ".cv-ref-doc--pdf .cv-ref__aside,.cv-ref-doc--pdf .cv-ref__main{display:table-cell !important;vertical-align:top !important;overflow:visible !important;}"
        ".cv-ref-doc--pdf .cv-ref__aside{width:32% !important;padding-right:1.2rem !important;}"
        ".cv-ref-doc--pdf .cv-ref__main{width:68% !important;}"
        ".cv-ref-doc--pdf .cv-ref__section,.cv-ref-doc--pdf .cv-ref__timeline-item,.cv-ref-doc--pdf .cv-ref__edu-item{break-inside:auto !important;page-break-inside:auto !important;}"
        "@page{size:A4;margin:0;}"
        "</style></head><body>"
        '<div class="preview-doc-stage"><div class="cv-paper">'
        '<div class="cv-paper-inner cv-ref-doc cv-ref-doc--pdf">'
        f"{preview_html}"
        "</div></div></div></body></html>"
    )


def _css_from_app(root_path: str) -> str:
    css_path = Path(root_path) / "static" / "css" / "app.css"
    try:
        return css_path.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"No se pudo leer CSS del preview: {css_path}") from e


def _render_html_to_pdf_with_weasyprint(html_doc: str) -> bytes:
    try:
        from weasyprint import HTML
    except Exception as e:  # pragma: no cover - dependencia opcional en runtime
        raise RuntimeError(
            "WeasyPrint no está disponible. Instala con: uv add weasyprint"
        ) from e
    try:
        return HTML(string=html_doc).write_pdf()
    except Exception as e:
        raise RuntimeError(f"WeasyPrint no pudo renderizar el PDF: {e}") from e


async def _render_html_to_pdf_with_playwright(html_doc: str) -> bytes:
    try:
        from playwright.async_api import async_playwright
    except Exception as e:  # pragma: no cover - dependencia opcional en runtime
        raise RuntimeError(
            "Playwright no está disponible. Instala con: uv add playwright "
            "y luego: uv run playwright install chromium"
        ) from e

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            page = await browser.new_page()
            await page.set_content(html_doc, wait_until="networkidle")
            return await page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
            )
        finally:
            await browser.close()


def context_to_pdf_bytes_from_preview(
    data: dict[str, Any],
    *,
    root_path: str,
    fallback_title: str = "",
) -> bytes:
    """
    Renderiza PDF desde el mismo HTML/CSS del preview (fiel al estilo/íconos).
    """
    css_text = _css_from_app(root_path)
    html_doc = context_to_preview_document_html(
        data,
        css_text=css_text,
        fallback_title=fallback_title,
    )
    # 1) WeasyPrint suele paginar columnas mejor para CV largos.
    try:
        return _render_html_to_pdf_with_weasyprint(html_doc)
    except RuntimeError:
        # 2) Fallback a Chromium/Playwright.
        return asyncio.run(_render_html_to_pdf_with_playwright(html_doc))


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


def context_to_pdf_bytes(
    data: dict[str, Any],
    *,
    fallback_title: str = "",
) -> bytes:
    """
    PDF estructurado inspirado en la vista previa (cabecera + dos columnas).
    No depende de Markdown para evitar drift y saltos extraños.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()

    font_path = _unicode_font_path()
    use_custom_font = bool(font_path)
    if use_custom_font:
        pdf.add_font("CvBody", "", str(font_path))
        font = "CvBody"
    else:
        font = "Helvetica"

    page_left = pdf.l_margin
    page_top = pdf.t_margin
    page_right = pdf.w - pdf.r_margin
    page_width = pdf.epw

    title_sz = 22
    subtitle_sz = 13
    section_sz = 9
    role_sz = 12
    body_sz = 10
    small_sz = 9
    lh = 5.2

    def txt(v: Any) -> str:
        s = "" if v is None else str(v)
        return _fold_latin_fallback(s) if not font_path else s

    def set_font(size: float, *, bold: bool = False) -> None:
        style = ""
        if bold and not use_custom_font:
            style = "B"
        pdf.set_font(font, style, size=size)

    def write_block(
        x: float,
        y: float,
        w: float,
        text: str,
        size: float,
        *,
        align: str = "L",
    ) -> float:
        text = txt(text).strip()
        if not text:
            return y
        set_font(size)
        pdf.set_xy(x, y)
        if XPos is not None and YPos is not None:
            pdf.multi_cell(
                w,
                lh,
                text,
                align=align,
                new_x=XPos.LEFT,
                new_y=YPos.NEXT,
            )
        else:
            pdf.multi_cell(w, lh, text, align=align)
        return pdf.get_y()

    def write_pills(x: float, y: float, w: float, items: list[str]) -> float:
        cur_x = x
        cur_y = y
        pill_h = 6
        pad_x = 1.8
        gap_x = 1.4
        gap_y = 1.4
        set_font(8)
        pdf.set_text_color(55, 65, 81)
        pdf.set_draw_color(209, 213, 219)
        pdf.set_fill_color(249, 250, 251)
        for raw in items:
            label = txt(raw).strip()
            if not label:
                continue
            pill_w = pdf.get_string_width(label) + (pad_x * 2)
            if cur_x + pill_w > x + w:
                cur_x = x
                cur_y += pill_h + gap_y
            pdf.set_xy(cur_x, cur_y)
            pdf.cell(pill_w, pill_h, label, border=1, ln=0, align="C", fill=True)
            cur_x += pill_w + gap_x
        pdf.set_text_color(17, 24, 39)
        return cur_y + pill_h

    def section_title(x: float, y: float, w: float, title: str) -> float:
        set_font(section_sz, bold=True)
        pdf.set_text_color(102, 112, 133)
        pdf.set_xy(x, y)
        t = txt(title).upper()
        if XPos is not None and YPos is not None:
            pdf.multi_cell(w, lh - 1, t, new_x=XPos.LEFT, new_y=YPos.NEXT)
        else:
            pdf.multi_cell(w, lh - 1, t)
        y = pdf.get_y()
        pdf.set_draw_color(229, 231, 235)
        pdf.line(x, y + 0.6, x + w, y + 0.6)
        pdf.set_text_color(17, 24, 39)
        return y + 2.0

    # Header
    meta = data.get("meta") or {}
    name = (meta.get("nombre_completo") or "").strip() or fallback_title.strip()
    subtitle = (meta.get("titulo_profesional") or "").strip() or (
        meta.get("objetivo_cv") or ""
    ).strip()
    contact = _contact_line(meta)

    y = page_top
    if name:
        set_font(title_sz, bold=True)
        pdf.set_text_color(17, 24, 39)
        pdf.set_xy(page_left, y)
        if XPos is not None and YPos is not None:
            pdf.multi_cell(
                page_width,
                8,
                txt(name).upper(),
                new_x=XPos.LEFT,
                new_y=YPos.NEXT,
            )
        else:
            pdf.multi_cell(page_width, 8, txt(name).upper())
        y = pdf.get_y()
    if subtitle:
        set_font(subtitle_sz, bold=False)
        pdf.set_text_color(30, 90, 140)
        y = write_block(page_left, y + 1, page_width, subtitle, subtitle_sz)
    if contact:
        set_font(small_sz)
        pdf.set_text_color(75, 85, 99)
        y += 1
        for label, val in contact:
            line = f"{label.upper()}  {val}"
            y = write_block(page_left, y, page_width, line, small_sz)
    y += 2
    pdf.set_draw_color(209, 213, 219)
    pdf.line(page_left, y, page_right, y)
    y += 4
    pdf.set_text_color(17, 24, 39)

    # Column geometry
    col_gap = 8
    aside_w = max(52.0, page_width * 0.34)
    main_w = page_width - aside_w - col_gap
    aside_x = page_left
    main_x = aside_x + aside_w + col_gap
    aside_y = y
    main_y = y

    # Aside content
    certs = data.get("certificaciones") or []
    if isinstance(certs, list) and certs:
        aside_y = section_title(aside_x, aside_y, aside_w, "Certificaciones")
        for c in certs:
            if isinstance(c, dict):
                name_c = (c.get("nombre") or c.get("titulo") or "").strip()
                desc_c = (c.get("descripcion") or c.get("detalle") or "").strip()
                if name_c:
                    set_font(body_sz, bold=True)
                    aside_y = write_block(aside_x, aside_y, aside_w, name_c, body_sz)
                if desc_c:
                    aside_y = write_block(aside_x, aside_y, aside_w, desc_c, small_sz)
            else:
                aside_y = write_block(aside_x, aside_y, aside_w, c, small_sz)
            aside_y += 1
        aside_y += 1

    strengths = data.get("fortalezas") or []
    if isinstance(strengths, list) and strengths:
        aside_y = section_title(aside_x, aside_y, aside_w, "Fortalezas")
        for s in strengths:
            if isinstance(s, dict):
                st = (s.get("titulo") or s.get("nombre") or "").strip()
                sd = (s.get("descripcion") or "").strip()
                line = st if not sd else f"{st}: {sd}" if st else sd
                if line:
                    aside_y = write_block(aside_x, aside_y, aside_w, f"• {line}", small_sz)
            else:
                aside_y = write_block(aside_x, aside_y, aside_w, f"• {s}", small_sz)
        aside_y += 2

    hab = data.get("habilidades") or {}
    perfil_kw = (data.get("perfil_profesional") or {}).get("palabras_clave") or []
    tech = _merge_tecnicas_lists(hab.get("tecnicas"), perfil_kw)
    soft = hab.get("blandas") or []
    langs = hab.get("idiomas") or []
    if tech or soft or langs:
        aside_y = section_title(aside_x, aside_y, aside_w, "Habilidades")
        if tech:
            set_font(small_sz, bold=True)
            aside_y = write_block(aside_x, aside_y, aside_w, "Técnicas", small_sz)
            aside_y = write_pills(aside_x, aside_y, aside_w, [str(t) for t in tech])
            aside_y += 1
        if soft:
            set_font(small_sz, bold=True)
            aside_y = write_block(aside_x, aside_y, aside_w, "Blandas", small_sz)
            for item in soft:
                aside_y = write_block(aside_x, aside_y, aside_w, f"• {item}", small_sz)
            aside_y += 1
        if langs:
            set_font(small_sz, bold=True)
            aside_y = write_block(aside_x, aside_y, aside_w, "Idiomas", small_sz)
            for item in langs:
                aside_y = write_block(aside_x, aside_y, aside_w, f"• {item}", small_sz)
            aside_y += 1

    # Main content
    perfil = data.get("perfil_profesional") or {}
    resumen = (perfil.get("resumen") or "").strip()
    if resumen:
        main_y = section_title(main_x, main_y, main_w, "Perfil profesional")
        main_y = write_block(main_x, main_y, main_w, resumen, body_sz)
        main_y += 2

    exp = data.get("experiencia") or []
    if isinstance(exp, list) and exp:
        main_y = section_title(main_x, main_y, main_w, "Experiencia")
        for item in exp:
            if not isinstance(item, dict):
                main_y = write_block(main_x, main_y, main_w, item, body_sz)
                continue
            cargo = (item.get("cargo") or "").strip()
            org = (item.get("empresa") or "").strip()
            drange = _exp_date_range(item)
            loc = (item.get("ubicacion") or "").strip()
            title_line = " · ".join(x for x in (cargo, org) if x)
            if cargo:
                set_font(role_sz, bold=True)
                main_y = write_block(main_x, main_y, main_w, cargo, role_sz)
            if org:
                pdf.set_text_color(30, 90, 140)
                main_y = write_block(main_x, main_y, main_w, org, body_sz)
                pdf.set_text_color(17, 24, 39)
            meta_line = " | ".join(x for x in (drange, loc) if x)
            if meta_line:
                pdf.set_text_color(107, 114, 128)
                main_y = write_block(main_x, main_y, main_w, meta_line, small_sz)
                pdf.set_text_color(17, 24, 39)
            for label, key in (("Responsabilidades", "responsabilidades"), ("Logros", "logros")):
                val = item.get(key)
                if not val:
                    continue
                set_font(small_sz, bold=True)
                main_y = write_block(main_x, main_y + 0.5, main_w, f"{label}:", small_sz)
                if isinstance(val, list):
                    for row in val:
                        main_y = write_block(main_x, main_y, main_w, f"• {row}", small_sz)
                else:
                    main_y = write_block(main_x, main_y, main_w, str(val), small_sz)
            main_y += 2

    edu = data.get("educacion") or []
    if isinstance(edu, list) and edu:
        main_y = section_title(main_x, main_y, main_w, "Educación")
        for item in edu:
            if not isinstance(item, dict):
                main_y = write_block(main_x, main_y, main_w, item, body_sz)
                continue
            titulo = (item.get("titulo") or "").strip()
            inst = (item.get("institucion") or "").strip()
            loc = (item.get("ubicacion") or "").strip()
            if titulo or inst:
                set_font(role_sz, bold=True)
                main_y = write_block(main_x, main_y, main_w, titulo, role_sz)
            if inst:
                pdf.set_text_color(30, 90, 140)
                main_y = write_block(main_x, main_y, main_w, inst, body_sz)
                pdf.set_text_color(17, 24, 39)
            extra: list[str] = []
            if item.get("fecha_inicio") or item.get("fecha_fin"):
                extra.append(
                    " – ".join(
                        x for x in (item.get("fecha_inicio") or "", item.get("fecha_fin") or "") if x
                    )
                )
            if item.get("estado"):
                extra.append(str(item.get("estado")))
            meta_line = " | ".join(x for x in (*extra, loc) if x)
            if meta_line:
                pdf.set_text_color(107, 114, 128)
                main_y = write_block(main_x, main_y, main_w, meta_line, small_sz)
                pdf.set_text_color(17, 24, 39)
            main_y += 1.5

    proy = data.get("proyectos") or []
    if isinstance(proy, list) and proy:
        main_y = section_title(main_x, main_y, main_w, "Proyectos")
        for item in proy:
            if not isinstance(item, dict):
                main_y = write_block(main_x, main_y, main_w, item, body_sz)
                continue
            name_p = (item.get("nombre") or "Proyecto").strip()
            set_font(role_sz, bold=True)
            main_y = write_block(main_x, main_y, main_w, name_p, role_sz)
            if item.get("descripcion"):
                main_y = write_block(main_x, main_y, main_w, str(item["descripcion"]), body_sz)
            tec = item.get("tecnologias")
            if isinstance(tec, list) and tec:
                main_y = write_block(main_x, main_y, main_w, "Tecnologías: " + ", ".join(str(t) for t in tec), small_sz)
            if item.get("enlace"):
                main_y = write_block(main_x, main_y, main_w, "Enlace: " + str(item["enlace"]), small_sz)
            main_y += 1.5

    return bytes(pdf.output())


def markdown_to_pdf_bytes(md: str) -> bytes:
    """
    Compatibilidad temporal: genera un PDF básico desde texto Markdown.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()
    font_path = _unicode_font_path()
    if font_path:
        pdf.add_font("CvBody", "", str(font_path))
        pdf.set_font("CvBody", size=10)
    else:
        pdf.set_font("Helvetica", size=10)
        md = _fold_latin_fallback(md)
    for raw in md.split("\n"):
        line = _strip_inline_markdown(raw.rstrip())
        if not line:
            pdf.ln(2)
            continue
        pdf.set_x(pdf.l_margin)
        if XPos is not None and YPos is not None:
            pdf.multi_cell(pdf.epw, 5, line, new_x=XPos.LEFT, new_y=YPos.NEXT)
        else:
            pdf.multi_cell(pdf.epw, 5, line)
    return bytes(pdf.output())
