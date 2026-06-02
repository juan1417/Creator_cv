"""Helpers to convert flat form data into a CV dict.

The HTML form posts flat keys like ``experiencia[0][empresa]`` and
``habilidades[tecnicas][]``. :func:`parse_form_to_cv` regroups them
into the nested structure expected by :class:`CVSchema`.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

# experiencia[0][empresa]  -> ("experiencia", 0, "empresa")
_LIST_ITEM_RE = re.compile(r"^([a-zA-Z_]+)\[(\d+)\]\[([a-zA-Z_]+)\]$")
# habilidades[tecnicas][]  -> ("habilidades", "tecnicas", None)
_LIST_APPEND_RE = re.compile(r"^([a-zA-Z_]+)\[([a-zA-Z_]+)\]\[\]$")


def _split_list_items(form: Mapping[str, Any]) -> tuple[dict[str, dict[int, dict[str, Any]]], list[str]]:
    """Pull ``foo[N][bar]`` keys into ``{foo: {N: {bar: value}}}``.

    Returns the extracted mapping and a list of key names consumed.
    Supports both flat dicts and ``MultiDict`` (uses ``getlist`` so
    repeated keys are all captured).
    """
    grouped: dict[str, dict[int, dict[str, Any]]] = {}
    consumed: list[str] = []
    for key in form:
        m = _LIST_ITEM_RE.match(key)
        if not m:
            continue
        section, idx, field = m.group(1), int(m.group(2)), m.group(3)
        values = _get_all(form, key)
        # Use the first value (the form only sends one value per slot).
        value = values[0] if values else ""
        grouped.setdefault(section, {}).setdefault(idx, {})[field] = _coerce(value)
        consumed.append(key)
    return grouped, consumed


def _split_list_appends(
    form: Mapping[str, Any],
) -> tuple[dict[str, dict[str, list[Any]]], list[str]]:
    """Pull ``foo[bar][]`` keys into ``{foo: {bar: [values]}}``.

    Repeated keys with ``[]`` accumulate as a list of values.
    """
    grouped: dict[str, dict[str, list[Any]]] = {}
    consumed: list[str] = []
    for key in form:
        m = _LIST_APPEND_RE.match(key)
        if not m:
            continue
        section, field = m.group(1), m.group(2)
        for value in _get_all(form, key):
            grouped.setdefault(section, {}).setdefault(field, []).append(_coerce(value))
        consumed.append(key)
    return grouped, consumed


def _get_all(form: Mapping[str, Any], key: str) -> list[Any]:
    """Like ``form.getlist(key)`` but works on plain dicts too."""
    if hasattr(form, "getlist"):
        return list(form.getlist(key))
    v = form.get(key)
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _coerce(value: Any) -> Any:
    """Coerce checkbox-on/off and strip whitespace on strings."""
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        if v == "":
            return ""
        return v
    return value


def parse_form_to_cv(form: Mapping[str, Any]) -> dict[str, Any]:
    """Convert flat form fields into a CV dict matching :class:`CVSchema`.

    The output may contain empty strings; ``validate_cv`` will normalize
    them into proper defaults.
    """
    items, _consumed_items = _split_list_items(form)
    appends, _consumed_appends = _split_list_appends(form)

    # --- nested items (experiencia, educacion, proyectos) ---
    experiencia = [
        _clean_item(items.get("experiencia", {}).get(i, {}), Experiencia_FIELDS)
        for i in sorted(items.get("experiencia", {}).keys())
    ]
    educacion = [
        _clean_item(items.get("educacion", {}).get(i, {}), Educacion_FIELDS)
        for i in sorted(items.get("educacion", {}).keys())
    ]
    proyectos = [
        _clean_item(items.get("proyectos", {}).get(i, {}), Proyecto_FIELDS)
        for i in sorted(items.get("proyectos", {}).keys())
    ]

    # --- chips (tecnicas, blandas, idiomas, certificaciones, fortalezas) ---
    habilidades = {
        "tecnicas": _non_empty(appends.get("habilidades", {}).get("tecnicas", [])),
        "blandas": _non_empty(appends.get("habilidades", {}).get("blandas", [])),
        "idiomas": _non_empty(appends.get("habilidades", {}).get("idiomas", [])),
    }
    certificaciones = _non_empty(appends.get("certificaciones", {}).get("items", []))
    fortalezas = _non_empty(appends.get("fortalezas", {}).get("items", []))

    # --- scalars (everything else) ---
    cv: dict[str, Any] = {
        "meta": {
            "nombre_completo": form.get("meta.nombre_completo", ""),
            "titulo_profesional": form.get("meta.titulo_profesional", "") or None,
            "contacto": {
                "email": form.get("meta.contacto.email", "") or None,
                "telefono": form.get("meta.contacto.telefono", "") or None,
                "linkedin": form.get("meta.contacto.linkedin", "") or None,
                "ubicacion": form.get("meta.contacto.ubicacion", "") or None,
            },
        },
        "perfil_profesional": {
            "resumen": form.get("perfil_profesional.resumen", ""),
            "palabras_clave": _split_csv(form.get("perfil_profesional.palabras_clave", "")),
        },
        "experiencia": experiencia,
        "educacion": educacion,
        "habilidades": habilidades,
        "proyectos": proyectos,
        "certificaciones": certificaciones,
        "fortalezas": fortalezas,
    }
    return cv


# --- internal helpers ---


Experiencia_FIELDS = (
    "empresa",
    "cargo",
    "ubicacion",
    "fecha_inicio",
    "fecha_fin",
    "actual",
    "responsabilidades",
    "logros",
)
Educacion_FIELDS = (
    "institucion",
    "titulo",
    "ubicacion",
    "fecha_inicio",
    "fecha_fin",
    "estado",
)
Proyecto_FIELDS = ("nombre", "descripcion", "tecnologias", "enlace")


def _clean_item(raw: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in fields:
        v = raw.get(f, "")
        if f in {"actual"}:
            out[f] = bool(v)
        elif f in {"responsabilidades", "logros"}:
            # One item per line
            out[f] = _split_lines(v) if isinstance(v, str) else _non_empty(v)
        elif f == "tecnologias":
            # Comma-separated string OR list of strings
            out[f] = _split_csv(v) if isinstance(v, str) else _non_empty(v)
        else:
            out[f] = (v or "") if isinstance(v, str) else v
    return out


def _split_lines(value: str) -> list[str]:
    if not value:
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]


def _split_csv(value: str) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def _non_empty(values: list[Any]) -> list[Any]:
    return [v for v in values if v not in (None, "", [])]
