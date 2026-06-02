"""CV renderers: PDF (Harvard-style), DOCX, and HTML preview.

All three consume a single CV dict matching :class:`creator_cv.schemas.CVSchema`.

The PDF uses fpdf2 + DejaVuSans for full Unicode support (tildes, ñ, etc.)
and follows a clean single-column Harvard layout:

* Header: name (16pt bold) + professional title (italic) + contact line.
* Sections in uppercase with a thin separator rule.
* Education listed before experience (per Harvard convention).
* Bullets for experience responsibilities / achievements.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from fpdf import FPDF

# --- Constants ---

_FONT_NAME = "DejaVu"
_FONT_PATH = (
    Path(__file__).resolve().parent / "static" / "fonts" / "DejaVuSans.ttf"
)
_FONT_BOLD_PATH = (
    Path(__file__).resolve().parent / "static" / "fonts" / "DejaVuSans-Bold.ttf"
)
_FONT_ITALIC_PATH = (
    Path(__file__).resolve().parent / "static" / "fonts" / "DejaVuSans-Oblique.ttf"
)
_FONT_BOLD_ITALIC_PATH = (
    Path(__file__).resolve().parent / "static" / "fonts" / "DejaVuSans-BoldOblique.ttf"
)


# =========================
# PDF
# =========================


def _ensure_fonts(pdf: FPDF) -> None:
    """Register the DejaVu font family once."""
    if not _FONT_PATH.exists():
        raise FileNotFoundError(
            f"Fuente Unicode no encontrada: {_FONT_PATH}. "
            "Descarga DejaVuSans.ttf a creator_cv/static/fonts/."
        )
    pdf.add_font(_FONT_NAME, "", str(_FONT_PATH))
    if _FONT_BOLD_PATH.exists():
        pdf.add_font(_FONT_NAME, "B", str(_FONT_BOLD_PATH))
    if _FONT_ITALIC_PATH.exists():
        pdf.add_font(_FONT_NAME, "I", str(_FONT_ITALIC_PATH))
    if _FONT_BOLD_ITALIC_PATH.exists():
        pdf.add_font(_FONT_NAME, "BI", str(_FONT_BOLD_ITALIC_PATH))


class _HarvardPDF(FPDF):
    def footer(self) -> None:  # noqa: D401 - FPDF callback
        self.set_y(-12)
        self.set_font(_FONT_NAME, "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Página {self.page_no()}", align="C")
        self.set_text_color(20, 20, 20)


def _safe_w(pdf: FPDF) -> float:
    """Width that fits within the current margins."""
    return pdf.w - pdf.l_margin - pdf.r_margin


def _draw_header(pdf: FPDF, cv: dict[str, Any]) -> None:
    meta = cv.get("meta") or {}
    contacto = meta.get("contacto") or {}

    name = (meta.get("nombre_completo") or "").strip() or "Nombre Apellido"
    title = (meta.get("titulo_profesional") or "").strip()

    # Name
    pdf.set_font(_FONT_NAME, "B", 16)
    pdf.set_text_color(20, 20, 20)
    pdf.set_x(pdf.l_margin)
    pdf.cell(_safe_w(pdf), 8, name, align="C", new_x="LMARGIN", new_y="NEXT")

    if title:
        pdf.set_font(_FONT_NAME, "I", 11)
        pdf.set_x(pdf.l_margin)
        pdf.cell(_safe_w(pdf), 6, title, align="C", new_x="LMARGIN", new_y="NEXT")

    bits = [
        (contacto.get("email") or "").strip(),
        (contacto.get("telefono") or "").strip(),
        (contacto.get("linkedin") or "").strip(),
        (contacto.get("ubicacion") or "").strip(),
    ]
    bits = [b for b in bits if b]
    if bits:
        pdf.set_font(_FONT_NAME, "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.set_x(pdf.l_margin)
        pdf.cell(_safe_w(pdf), 5, " | ".join(bits), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(20, 20, 20)

    resumen = (cv.get("perfil_profesional") or {}).get("resumen") or ""
    if resumen.strip():
        pdf.ln(4)
        pdf.set_font(_FONT_NAME, "", 10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(_safe_w(pdf), 4.8, resumen.strip())
        pdf.ln(2)

    pdf.ln(2)


def _section_heading(pdf: FPDF, title: str) -> None:
    pdf.set_font(_FONT_NAME, "B", 10.5)
    pdf.set_text_color(40, 40, 40)
    pdf.set_x(pdf.l_margin)
    pdf.cell(_safe_w(pdf), 6, title, new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y()
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(2)
    pdf.set_text_color(20, 20, 20)


def _date_range(exp: dict[str, Any]) -> str:
    start = (exp.get("fecha_inicio") or "").strip()
    end = (exp.get("fecha_fin") or "").strip()
    if exp.get("actual"):
        end = "Actualidad"
    if start and end:
        return f"{start} — {end}"
    return start or end or ""


def _draw_experiencia(pdf: FPDF, items: list[dict[str, Any]]) -> None:
    for exp in items:
        cargo = (exp.get("cargo") or "").strip()
        empresa = (exp.get("empresa") or "").strip()
        ubicacion = (exp.get("ubicacion") or "").strip()
        dates = _date_range(exp)

        # First line: cargo (bold) left, dates (regular) right.
        pdf.set_x(pdf.l_margin)
        pdf.set_font(_FONT_NAME, "B", 10.5)
        left = cargo or empresa
        if left:
            pdf.cell(_safe_w(pdf) - 50, 5, left, new_x="END")
        if dates:
            pdf.set_font(_FONT_NAME, "", 9.5)
            pdf.set_text_color(90, 90, 90)
            pdf.cell(50, 5, dates, align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(20, 20, 20)
        else:
            pdf.ln(5)

        if empresa and empresa != cargo:
            line = f"{empresa} — {ubicacion}" if ubicacion else empresa
            pdf.set_x(pdf.l_margin)
            pdf.set_font(_FONT_NAME, "I", 9.5)
            pdf.cell(_safe_w(pdf), 4.5, line, new_x="LMARGIN", new_y="NEXT")

        bullets: list[str] = list(exp.get("responsabilidades") or []) + list(exp.get("logros") or [])
        bullets = [b for b in bullets if b and b.strip()]
        if bullets:
            pdf.set_font(_FONT_NAME, "", 9.5)
            for b in bullets:
                pdf.set_x(pdf.l_margin + 4)
                pdf.multi_cell(_safe_w(pdf) - 4, 4.4, f"• {b.strip()}")
        pdf.ln(2)


def _draw_educacion(pdf: FPDF, items: list[dict[str, Any]]) -> None:
    for ed in items:
        institucion = (ed.get("institucion") or "").strip()
        titulo = (ed.get("titulo") or "").strip()
        ubicacion = (ed.get("ubicacion") or "").strip()
        estado = (ed.get("estado") or "").strip()
        start = (ed.get("fecha_inicio") or "").strip()
        end = (ed.get("fecha_fin") or "").strip()
        dates = f"{start} — {end}" if start or end else ""

        pdf.set_x(pdf.l_margin)
        pdf.set_font(_FONT_NAME, "B", 10.5)
        if institucion:
            pdf.cell(_safe_w(pdf) - 50, 5, institucion, new_x="END")
        if dates:
            pdf.set_font(_FONT_NAME, "", 9.5)
            pdf.set_text_color(90, 90, 90)
            pdf.cell(50, 5, dates, align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(20, 20, 20)
        else:
            pdf.ln(5)

        if titulo or estado:
            line_parts = [p for p in [titulo, estado] if p]
            pdf.set_x(pdf.l_margin)
            pdf.set_font(_FONT_NAME, "I", 9.5)
            pdf.cell(_safe_w(pdf), 4.5, " — ".join(line_parts), new_x="LMARGIN", new_y="NEXT")

        if ubicacion:
            pdf.set_x(pdf.l_margin)
            pdf.set_font(_FONT_NAME, "", 9)
            pdf.set_text_color(110, 110, 110)
            pdf.cell(_safe_w(pdf), 4, ubicacion, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(20, 20, 20)
        pdf.ln(1.5)


def _draw_proyectos(pdf: FPDF, items: list[dict[str, Any]]) -> None:
    for p in items:
        nombre = (p.get("nombre") or "").strip()
        desc = (p.get("descripcion") or "").strip()
        techs = [t for t in (p.get("tecnologias") or []) if t]
        enlace = (p.get("enlace") or "").strip()

        if nombre:
            pdf.set_x(pdf.l_margin)
            pdf.set_font(_FONT_NAME, "B", 10.5)
            pdf.cell(_safe_w(pdf), 5, nombre, new_x="LMARGIN", new_y="NEXT")

        if desc:
            pdf.set_x(pdf.l_margin)
            pdf.set_font(_FONT_NAME, "", 9.5)
            pdf.multi_cell(_safe_w(pdf), 4.4, desc)

        if techs:
            pdf.set_x(pdf.l_margin)
            pdf.set_font(_FONT_NAME, "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(_safe_w(pdf), 4.2, "Tecnologías: " + ", ".join(techs))
            pdf.set_text_color(20, 20, 20)

        if enlace:
            pdf.set_x(pdf.l_margin)
            pdf.set_font(_FONT_NAME, "", 9)
            pdf.set_text_color(30, 80, 160)
            pdf.cell(_safe_w(pdf), 4, enlace, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(20, 20, 20)
        pdf.ln(1.5)


def _draw_simple_list(pdf: FPDF, items: list[str]) -> None:
    pdf.set_font(_FONT_NAME, "", 9.5)
    for it in items:
        s = (it or "").strip()
        if not s:
            continue
        pdf.set_x(pdf.l_margin + 4)
        pdf.multi_cell(_safe_w(pdf) - 4, 4.4, f"• {s}")
    pdf.ln(1.5)


def render_pdf(cv: dict[str, Any]) -> bytes:
    """Render the CV to PDF bytes (Harvard-style, single column)."""
    pdf = _HarvardPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    _ensure_fonts(pdf)
    pdf.add_page()

    _draw_header(pdf, cv)

    experiencia = list(cv.get("experiencia") or [])
    educacion = list(cv.get("educacion") or [])
    proyectos = list(cv.get("proyectos") or [])
    habilidades = cv.get("habilidades") or {}
    certificaciones = list(cv.get("certificaciones") or [])
    fortalezas = list(cv.get("fortalezas") or [])

    if educacion:
        _section_heading(pdf, "EDUCACIÓN")
        _draw_educacion(pdf, educacion)

    if experiencia:
        _section_heading(pdf, "EXPERIENCIA")
        _draw_experiencia(pdf, experiencia)

    if proyectos:
        _section_heading(pdf, "PROYECTOS")
        _draw_proyectos(pdf, proyectos)

    tecnicas = list(habilidades.get("tecnicas") or [])
    if tecnicas:
        _section_heading(pdf, "HABILIDADES TÉCNICAS")
        _draw_simple_list(pdf, tecnicas)

    if certificaciones:
        _section_heading(pdf, "CERTIFICACIONES")
        _draw_simple_list(pdf, certificaciones)

    idiomas = list(habilidades.get("idiomas") or [])
    if idiomas:
        _section_heading(pdf, "IDIOMAS")
        _draw_simple_list(pdf, idiomas)

    if fortalezas:
        _section_heading(pdf, "FORTALEZAS")
        _draw_simple_list(pdf, fortalezas)

    return bytes(pdf.output())


# =========================
# DOCX
# =========================


def render_docx(cv: dict[str, Any]) -> bytes:
    """Render the CV to DOCX bytes."""
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    meta = cv.get("meta") or {}
    contacto = meta.get("contacto") or {}

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(meta.get("nombre_completo") or "Nombre Apellido")
    run.bold = True
    run.font.size = Pt(16)

    if meta.get("titulo_profesional"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(meta["titulo_profesional"])
        run.italic = True
        run.font.size = Pt(11)

    bits = [
        (contacto.get("email") or "").strip(),
        (contacto.get("telefono") or "").strip(),
        (contacto.get("linkedin") or "").strip(),
        (contacto.get("ubicacion") or "").strip(),
    ]
    bits = [b for b in bits if b]
    if bits:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(" | ".join(bits))
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    resumen = (cv.get("perfil_profesional") or {}).get("resumen") or ""
    if resumen.strip():
        doc.add_paragraph(resumen.strip())

    educacion = list(cv.get("educacion") or [])
    experiencia = list(cv.get("experiencia") or [])
    proyectos = list(cv.get("proyectos") or [])
    habilidades = cv.get("habilidades") or {}
    certificaciones = list(cv.get("certificaciones") or [])
    fortalezas = list(cv.get("fortalezas") or [])

    if educacion:
        doc.add_heading("EDUCACIÓN", level=1)
        for ed in educacion:
            p = doc.add_paragraph()
            run = p.add_run(ed.get("institucion") or "")
            run.bold = True
            start = (ed.get("fecha_inicio") or "").strip()
            end = (ed.get("fecha_fin") or "").strip()
            dates = f" — {start} — {end}" if start or end else ""
            if dates:
                run2 = p.add_run(dates)
                run2.italic = True
            if ed.get("titulo"):
                p2 = doc.add_paragraph()
                run = p2.add_run(ed["titulo"])
                run.italic = True
            if ed.get("estado"):
                doc.add_paragraph(ed["estado"])
            if ed.get("ubicacion"):
                p4 = doc.add_paragraph()
                run = p4.add_run(ed["ubicacion"])
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    if experiencia:
        doc.add_heading("EXPERIENCIA", level=1)
        for exp in experiencia:
            p = doc.add_paragraph()
            cargo = (exp.get("cargo") or "").strip()
            empresa = (exp.get("empresa") or "").strip()
            run = p.add_run(cargo or empresa)
            run.bold = True
            start = (exp.get("fecha_inicio") or "").strip()
            end = "Actualidad" if exp.get("actual") else (exp.get("fecha_fin") or "").strip()
            dates = f" — {start} — {end}" if start or end else ""
            if dates:
                run2 = p.add_run(dates)
                run2.italic = True
            if empresa and empresa != cargo:
                p2 = doc.add_paragraph()
                run = p2.add_run(empresa)
                run.italic = True
                if exp.get("ubicacion"):
                    run2 = p2.add_run(f" — {exp['ubicacion']}")
            for b in list(exp.get("responsabilidades") or []) + list(exp.get("logros") or []):
                if b and b.strip():
                    doc.add_paragraph(b.strip(), style="List Bullet")

    if proyectos:
        doc.add_heading("PROYECTOS", level=1)
        for pr in proyectos:
            p = doc.add_paragraph()
            run = p.add_run(pr.get("nombre") or "")
            run.bold = True
            if pr.get("descripcion"):
                doc.add_paragraph(pr["descripcion"])
            if pr.get("tecnologias"):
                p2 = doc.add_paragraph()
                run = p2.add_run("Tecnologías: " + ", ".join(pr["tecnologias"]))
                run.italic = True
                run.font.size = Pt(9)
            if pr.get("enlace"):
                doc.add_paragraph(pr["enlace"])

    tecnicas = list(habilidades.get("tecnicas") or [])
    if tecnicas:
        doc.add_heading("HABILIDADES TÉCNICAS", level=1)
        doc.add_paragraph(", ".join(tecnicas))

    if certificaciones:
        doc.add_heading("CERTIFICACIONES", level=1)
        for c in certificaciones:
            doc.add_paragraph(c, style="List Bullet")

    idiomas = list(habilidades.get("idiomas") or [])
    if idiomas:
        doc.add_heading("IDIOMAS", level=1)
        doc.add_paragraph(", ".join(idiomas))

    if fortalezas:
        doc.add_heading("FORTALEZAS", level=1)
        for f in fortalezas:
            doc.add_paragraph(f, style="List Bullet")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# =========================
# HTML (preview, used by Jinja)
# =========================


def render_html(cv: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized CV dict ready for the preview template."""
    return {
        "meta": cv.get("meta") or {},
        "perfil_profesional": cv.get("perfil_profesional") or {},
        "experiencia": list(cv.get("experiencia") or []),
        "educacion": list(cv.get("educacion") or []),
        "habilidades": cv.get("habilidades") or {},
        "proyectos": list(cv.get("proyectos") or []),
        "certificaciones": list(cv.get("certificaciones") or []),
        "fortalezas": list(cv.get("fortalezas") or []),
    }


__all__ = ["render_pdf", "render_docx", "render_html"]
