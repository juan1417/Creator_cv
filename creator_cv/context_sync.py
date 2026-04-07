from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from flask import Flask

_PKG_DIR = Path(__file__).resolve().parent
_ROOT = _PKG_DIR.parent

DEFAULT_REL_ACTIVE = Path("mcp-ia-preguntas/context/cv-context.active.json")
TEMPLATE_REL = Path("mcp-ia-preguntas/context/cv-context.template.json")

# Debe coincidir con las claves de raíz de `cv-context.template.json`.
EXPECTED_TOP_KEYS = frozenset(
    {
        "meta",
        "certificaciones",
        "fortalezas",
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


def default_active_context_path() -> Path:
    return _ROOT / DEFAULT_REL_ACTIVE


def default_template_path() -> Path:
    return _ROOT / TEMPLATE_REL


def get_active_context_path(app: Flask) -> Path:
    raw = app.config.get("CREATOR_CV_CONTEXT_PATH")
    if raw:
        return Path(str(raw)).expanduser().resolve()
    return default_active_context_path()


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


def merge_context_with_template(user: dict[str, Any]) -> dict[str, Any]:
    """
    Rellena claves y subobjetos faltantes con la plantilla oficial.
    Los valores del usuario siempre prevalecen.
    """
    base = copy.deepcopy(load_template_defaults())
    return _deep_merge(base, user)


def _deep_merge(base: Any, user: Any) -> Any:
    if isinstance(base, dict) and isinstance(user, dict):
        out = dict(base)
        for key, uval in user.items():
            if key in out and isinstance(out[key], dict) and isinstance(uval, dict):
                out[key] = _deep_merge(out[key], uval)
            else:
                out[key] = uval
        return out
    return user


def read_context_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        data = load_template_defaults()
        validate_context_shape(data)
        return data
    with path.open(encoding="utf-8") as f:
        parsed = json.load(f)
    if not isinstance(parsed, dict):
        raise ValueError("El contexto debe ser un objeto JSON (raíz: objeto).")
    data = merge_context_with_template(parsed)
    validate_context_shape(data)
    return data


def write_context_file(path: Path, data: dict[str, Any]) -> None:
    validate_context_shape(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(data, ensure_ascii=False, indent=2)
    tmp.write_text(text + "\n", encoding="utf-8")
    tmp.replace(path)


def parse_cv_context_json(raw: str | None) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        data = load_template_defaults()
        validate_context_shape(data)
        return data
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {e}") from e
    if not isinstance(parsed, dict):
        raise ValueError("El contexto debe ser un objeto JSON (raíz: objeto).")
    data = merge_context_with_template(parsed)
    validate_context_shape(data)
    return data
