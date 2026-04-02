"""
Flujo de preguntas guiadas alineado con el esquema mcp-ia-preguntas.
No inventa datos: solo guarda lo que la persona escribe.
"""

from __future__ import annotations

from typing import Any


STEP_ORDER = [
    "intro",
    "meta",
    "perfil",
    "experiencia",
    "educacion",
    "habilidades",
    "proyectos",
    "recursos",
    "restricciones",
    "dudas",
    "fin",
]


def step_index(step_id: str) -> int:
    try:
        return STEP_ORDER.index(step_id)
    except ValueError:
        return 0


def normalize_step(raw: str | None) -> str:
    if not raw or raw not in STEP_ORDER:
        return STEP_ORDER[0]
    return raw


def next_step_id(current: str) -> str | None:
    i = step_index(current)
    if i + 1 < len(STEP_ORDER):
        return STEP_ORDER[i + 1]
    return None


def prev_step_id(current: str) -> str | None:
    i = step_index(current)
    if i > 0:
        return STEP_ORDER[i - 1]
    return None


def _lines(s: str) -> list[str]:
    return [ln.strip() for ln in s.splitlines() if ln.strip()]


def _comma_list(s: str) -> list[str]:
    parts = []
    for chunk in s.replace("\n", ",").split(","):
        t = chunk.strip()
        if t:
            parts.append(t)
    return parts


def _ensure_nested(data: dict[str, Any]) -> None:
    data.setdefault("meta", {})
    data.setdefault("perfil_profesional", {"resumen": "", "palabras_clave": []})
    data.setdefault("experiencia", [])
    data.setdefault("educacion", [])
    data.setdefault(
        "habilidades",
        {"tecnicas": [], "blandas": [], "idiomas": []},
    )
    data.setdefault("proyectos", [])
    data.setdefault(
        "recursos_actuales",
        {"cv_existente": False, "texto_cv": "", "links": []},
    )
    data.setdefault(
        "restricciones",
        {
            "extension_maxima_paginas": None,
            "formato_solicitado": "",
            "otro": "",
        },
    )
    data.setdefault("dudas_pendientes", [])


def build_step_context(step_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Contexto para plantilla Jinja (título, textos de ayuda, valores actuales)."""
    _ensure_nested(data)
    meta = data["meta"]
    perfil = data["perfil_profesional"]
    hab = data["habilidades"]
    rec = data["recursos_actuales"]
    rest = data["restricciones"]

    ctx: dict[str, Any] = {
        "step_id": step_id,
        "step_title": "",
        "lede": "",
        "questions": [],
    }

    ctx.setdefault("fields", [])
    ctx.setdefault("allow_skip", False)
    ctx.setdefault("only_continue", False)
    ctx.setdefault("show_finish", False)
    ctx.setdefault("show_nav_buttons", False)

    if step_id == "intro":
        ctx["step_title"] = "Asistente de contexto"
        ctx["lede"] = (
            "Te haré unas preguntas cortas (varias pantallas). "
            "Lo que respondas se guardará en el JSON del CV; puedes dejar campos "
            "vacíos o usar «Saltar» cuando no aplique."
        )
        ctx["show_nav_buttons"] = True
        ctx["only_continue"] = True

    elif step_id == "meta":
        ctx["step_title"] = "Objetivo e idioma"
        ctx["questions"] = [
            "¿En qué idioma quieres el CV?",
            "¿Cuál es tu objetivo principal? (ej. tipo de rol, mercado, empresa)",
            "Opcional: tipo de CV y nivel aproximado.",
        ]
        ctx["fields"] = [
            {
                "name": "idioma_cv",
                "label": "Idioma del CV",
                "type": "text",
                "value": meta.get("idioma_cv") or "",
                "hint": "Ej. español, inglés",
            },
            {
                "name": "objetivo_cv",
                "label": "Objetivo",
                "type": "textarea",
                "value": meta.get("objetivo_cv") or "",
                "hint": "",
            },
            {
                "name": "tipo_cv",
                "label": "Tipo de CV (opcional)",
                "type": "text",
                "value": meta.get("tipo_cv") or "",
                "hint": "cronológico, funcional o mixto",
            },
            {
                "name": "nivel_seniority",
                "label": "Nivel (opcional)",
                "type": "text",
                "value": meta.get("nivel_seniority") or "",
                "hint": "ej. junior, semi-senior, senior",
            },
        ]

    elif step_id == "perfil":
        ctx["step_title"] = "Perfil profesional"
        ctx["questions"] = [
            "Resume en pocas frases tu perfil (solo hechos que quieras incluir).",
            "Palabras clave separadas por comas (stack, dominios).",
        ]
        kw = perfil.get("palabras_clave") or []
        ctx["fields"] = [
            {
                "name": "resumen",
                "label": "Resumen",
                "type": "textarea",
                "value": perfil.get("resumen") or "",
                "hint": "",
            },
            {
                "name": "palabras_clave",
                "label": "Palabras clave",
                "type": "text",
                "value": ", ".join(str(x) for x in kw),
                "hint": "Separadas por comas",
            },
        ]

    elif step_id == "experiencia":
        ctx["step_title"] = "Experiencia laboral"
        ctx["questions"] = [
            "Añade un puesto. Puedes repetir este paso más tarde desde el editor JSON "
            "o volver atrás. Si ahora no aplica, usa «Saltar».",
        ]
        ctx["fields"] = [
            {"name": "empresa", "label": "Empresa", "type": "text", "value": "", "hint": ""},
            {"name": "cargo", "label": "Cargo", "type": "text", "value": "", "hint": ""},
            {"name": "ubicacion", "label": "Ubicación (opcional)", "type": "text", "value": "", "hint": ""},
            {"name": "fecha_inicio", "label": "Fecha inicio", "type": "text", "value": "", "hint": "ej. 2020-03"},
            {"name": "fecha_fin", "label": "Fecha fin (si aplica)", "type": "text", "value": "", "hint": ""},
            {
                "name": "actual",
                "label": "Trabajo actual",
                "type": "checkbox",
                "value": False,
                "hint": "Marca si sigues en este puesto",
            },
            {
                "name": "responsabilidades",
                "label": "Responsabilidades (una por línea)",
                "type": "textarea",
                "value": "",
                "hint": "",
            },
            {
                "name": "logros",
                "label": "Logros (uno por línea; solo métricas que quieras incluir)",
                "type": "textarea",
                "value": "",
                "hint": "",
            },
        ]
        ctx["allow_skip"] = True

    elif step_id == "educacion":
        ctx["step_title"] = "Formación"
        ctx["questions"] = [
            "Añade un registro de educación (título, centro, fechas). «Saltar» si prefieres añadirlo luego.",
        ]
        ctx["fields"] = [
            {"name": "institucion", "label": "Institución", "type": "text", "value": "", "hint": ""},
            {"name": "titulo", "label": "Título / carrera", "type": "text", "value": "", "hint": ""},
            {"name": "ubicacion", "label": "Ubicación (opcional)", "type": "text", "value": "", "hint": ""},
            {"name": "fecha_inicio", "label": "Inicio", "type": "text", "value": "", "hint": ""},
            {"name": "fecha_fin", "label": "Fin", "type": "text", "value": "", "hint": ""},
            {
                "name": "estado",
                "label": "Estado",
                "type": "text",
                "value": "",
                "hint": "ej. completo, en curso",
            },
        ]
        ctx["allow_skip"] = True

    elif step_id == "habilidades":
        ctx["step_title"] = "Habilidades"
        ctx["questions"] = [
            "Lista habilidades técnicas, blandas e idiomas (separadas por comas).",
        ]
        ctx["fields"] = [
            {
                "name": "tecnicas",
                "label": "Técnicas",
                "type": "text",
                "value": ", ".join(str(x) for x in (hab.get("tecnicas") or [])),
                "hint": "",
            },
            {
                "name": "blandas",
                "label": "Blandas",
                "type": "text",
                "value": ", ".join(str(x) for x in (hab.get("blandas") or [])),
                "hint": "",
            },
            {
                "name": "idiomas",
                "label": "Idiomas",
                "type": "text",
                "value": ", ".join(str(x) for x in (hab.get("idiomas") or [])),
                "hint": "ej. Inglés C1, Español nativo",
            },
        ]

    elif step_id == "proyectos":
        ctx["step_title"] = "Proyectos"
        ctx["questions"] = [
            "Opcional: un proyecto destacado (nombre, descripción, tecnologías, enlace).",
        ]
        ctx["fields"] = [
            {"name": "nombre", "label": "Nombre", "type": "text", "value": "", "hint": ""},
            {
                "name": "descripcion",
                "label": "Descripción",
                "type": "textarea",
                "value": "",
                "hint": "",
            },
            {
                "name": "tecnologias",
                "label": "Tecnologías (comas)",
                "type": "text",
                "value": "",
                "hint": "",
            },
            {"name": "enlace", "label": "Enlace (opcional)", "type": "text", "value": "", "hint": ""},
        ]
        ctx["allow_skip"] = True

    elif step_id == "recursos":
        ctx["step_title"] = "Material que ya tienes"
        ctx["questions"] = [
            "¿Tienes un CV anterior o notas pegadas? Todo es opcional.",
        ]
        links = rec.get("links") or []
        ctx["fields"] = [
            {
                "name": "cv_existente",
                "label": "Ya tengo borrador o CV previo",
                "type": "checkbox",
                "value": bool(rec.get("cv_existente")),
                "hint": "",
            },
            {
                "name": "texto_cv",
                "label": "Pega aquí texto de referencia (opcional)",
                "type": "textarea",
                "value": rec.get("texto_cv") or "",
                "hint": "",
            },
            {
                "name": "links",
                "label": "Enlaces (uno por línea)",
                "type": "textarea",
                "value": "\n".join(str(x) for x in links),
                "hint": "LinkedIn, portfolio, etc.",
            },
        ]

    elif step_id == "restricciones":
        ctx["step_title"] = "Restricciones del CV"
        ctx["questions"] = [
            "Límites de extensión, formato pedido por la oferta u otras notas.",
        ]
        ext = rest.get("extension_maxima_paginas")
        ctx["fields"] = [
            {
                "name": "extension_maxima_paginas",
                "label": "Máximo de páginas (número o vacío)",
                "type": "text",
                "value": "" if ext is None else str(ext),
                "hint": "",
            },
            {
                "name": "formato_solicitado",
                "label": "Formato solicitado",
                "type": "text",
                "value": rest.get("formato_solicitado") or "",
                "hint": "ej. PDF, una página",
            },
            {
                "name": "otro",
                "label": "Otras restricciones",
                "type": "textarea",
                "value": rest.get("otro") or "",
                "hint": "",
            },
        ]

    elif step_id == "dudas":
        ctx["step_title"] = "Dudas pendientes"
        ctx["questions"] = [
            "¿Hay datos que aún no recuerdas o quieres confirmar más tarde? "
            "Una por línea.",
        ]
        dudas = data.get("dudas_pendientes") or []
        ctx["fields"] = [
            {
                "name": "dudas_pendientes",
                "label": "Dudas / pendientes",
                "type": "textarea",
                "value": "\n".join(str(x) for x in dudas),
                "hint": "Ej. fechas exactas en empresa X",
            },
        ]

    elif step_id == "fin":
        ctx["step_title"] = "Listo"
        ctx["lede"] = (
            "El contexto JSON se ha ido guardando en cada paso. Puedes revisarlo "
            "en el editor, exportarlo al archivo MCP o seguir completando datos."
        )
        ctx["show_finish"] = True

    return ctx


def apply_step(
    step_id: str,
    form: Any,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Fusiona el POST del paso actual en data. form: werkzeug MultiDict-like."""
    _ensure_nested(data)
    action = (form.get("action") or "next").strip().lower()

    if step_id == "intro":
        return data

    if action == "skip" and step_id in (
        "experiencia",
        "educacion",
        "proyectos",
    ):
        return data

    if step_id == "meta":
        data["meta"]["idioma_cv"] = (form.get("idioma_cv") or "").strip()
        data["meta"]["objetivo_cv"] = (form.get("objetivo_cv") or "").strip()
        data["meta"]["tipo_cv"] = (form.get("tipo_cv") or "").strip()
        data["meta"]["nivel_seniority"] = (form.get("nivel_seniority") or "").strip()

    elif step_id == "perfil":
        data["perfil_profesional"]["resumen"] = (form.get("resumen") or "").strip()
        data["perfil_profesional"]["palabras_clave"] = _comma_list(
            form.get("palabras_clave") or ""
        )

    elif step_id == "experiencia" and action != "skip":
        empresa = (form.get("empresa") or "").strip()
        cargo = (form.get("cargo") or "").strip()
        if not (empresa or cargo):
            return data
        entry = {
            "empresa": empresa,
            "cargo": cargo,
            "ubicacion": (form.get("ubicacion") or "").strip(),
            "fecha_inicio": (form.get("fecha_inicio") or "").strip(),
            "fecha_fin": (form.get("fecha_fin") or "").strip(),
            "actual": form.get("actual") == "1",
            "responsabilidades": _lines(form.get("responsabilidades") or ""),
            "logros": _lines(form.get("logros") or ""),
        }
        data["experiencia"].append(entry)

    elif step_id == "educacion" and action != "skip":
        inst = (form.get("institucion") or "").strip()
        tit = (form.get("titulo") or "").strip()
        if not (inst or tit):
            return data
        data["educacion"].append(
            {
                "institucion": inst,
                "titulo": tit,
                "ubicacion": (form.get("ubicacion") or "").strip(),
                "fecha_inicio": (form.get("fecha_inicio") or "").strip(),
                "fecha_fin": (form.get("fecha_fin") or "").strip(),
                "estado": (form.get("estado") or "").strip(),
            }
        )

    elif step_id == "habilidades":
        data["habilidades"]["tecnicas"] = _comma_list(form.get("tecnicas") or "")
        data["habilidades"]["blandas"] = _comma_list(form.get("blandas") or "")
        data["habilidades"]["idiomas"] = _comma_list(form.get("idiomas") or "")

    elif step_id == "proyectos" and action != "skip":
        nombre = (form.get("nombre") or "").strip()
        if not nombre and not (form.get("descripcion") or "").strip():
            return data
        tech_raw = form.get("tecnologias") or ""
        data["proyectos"].append(
            {
                "nombre": nombre or "",
                "descripcion": (form.get("descripcion") or "").strip(),
                "tecnologias": _comma_list(tech_raw),
                "enlace": (form.get("enlace") or "").strip(),
            }
        )

    elif step_id == "recursos":
        data["recursos_actuales"]["cv_existente"] = form.get("cv_existente") == "1"
        data["recursos_actuales"]["texto_cv"] = (form.get("texto_cv") or "").strip()
        data["recursos_actuales"]["links"] = _lines(form.get("links") or "")

    elif step_id == "restricciones":
        ext_raw = (form.get("extension_maxima_paginas") or "").strip()
        if ext_raw:
            try:
                data["restricciones"]["extension_maxima_paginas"] = int(ext_raw)
            except ValueError:
                data["restricciones"]["extension_maxima_paginas"] = None
        else:
            data["restricciones"]["extension_maxima_paginas"] = None
        data["restricciones"]["formato_solicitado"] = (
            form.get("formato_solicitado") or ""
        ).strip()
        data["restricciones"]["otro"] = (form.get("otro") or "").strip()

    elif step_id == "dudas":
        data["dudas_pendientes"] = _lines(form.get("dudas_pendientes") or "")

    return data
