from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PKG_DIR = Path(__file__).resolve().parent
_ROOT = _PKG_DIR.parent

TEMPLATE_REL = Path("mcp-ia-preguntas/context/cv-context.template.json")

EXPECTED_TOP_KEYS = frozenset(
    {
        "meta",
        "perfil_profesional",
        "experiencia",
        "educacion",
        "habilidades",
        "proyectos",
        "recursos_actuales",
        "restricciones",
        "dudas_pendientes",
    }
)


def project_root() -> Path:
    return _ROOT


def default_template_path() -> Path:
    return _ROOT / TEMPLATE_REL


def load_template_defaults() -> dict[str, Any]:
    p = default_template_path()
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def validate_context_shape(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("El contexto debe ser un objeto JSON (raíz: objeto).")
    keys = set(data.keys())
    missing = EXPECTED_TOP_KEYS - keys
    if missing:
        raise ValueError(
            "Faltan claves del esquema MCP: " + ", ".join(sorted(missing))
        )


def parse_cv_context_json(raw: str | None) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        data = load_template_defaults()
        validate_context_shape(data)
        return data
    data = json.loads(raw)
    validate_context_shape(data)
    return data

