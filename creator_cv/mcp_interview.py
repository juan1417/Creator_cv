"""
Entrevista impulsada por archivo JSON que la IA escribe vía MCP (Filesystem).

La IA coloca la siguiente pregunta y reglas de merge en `cv-interview.pending.json`;
esta app renderiza el Markdown, aplica respuestas al contexto CV y acumula review.md.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import markdown as md_lib
from flask import Flask

from creator_cv.context_sync import EXPECTED_TOP_KEYS, validate_context_shape

_PKG_DIR = Path(__file__).resolve().parent
_ROOT = _PKG_DIR.parent

PENDING_REL = Path("mcp-ia-preguntas/context/cv-interview.pending.json")
REVIEW_REL_PATTERN = "cv-review-cv{id}.active.md"

LIST_APPEND_ROOTS = frozenset(
    {"experiencia", "educacion", "proyectos", "dudas_pendientes"}
)


def get_pending_interview_path(app: Flask) -> Path:
    raw = app.config.get("CREATOR_CV_INTERVIEW_PENDING_PATH")
    if raw:
        return Path(str(raw)).expanduser().resolve()
    return _ROOT / PENDING_REL


def get_review_markdown_path(app: Flask, cv_id: int) -> Path:
    raw = app.config.get("CREATOR_CV_REVIEW_PATH")
    if raw:
        path = Path(str(raw)).expanduser()
        s = str(path)
        if "{id}" in s:
            return Path(s.replace("{id}", str(cv_id))).resolve()
        return path.resolve()
    return _ROOT / "mcp-ia-preguntas/context" / REVIEW_REL_PATTERN.format(id=cv_id)


def pending_template_path() -> Path:
    return _ROOT / Path("mcp-ia-preguntas/context/cv-interview.pending.template.json")


class PendingInterviewError(ValueError):
    pass


def _path_root(path: str) -> str:
    return path.strip().split(".", 1)[0]


def _validate_path_roots(paths: list[str]) -> None:
    for p in paths:
        root = _path_root(p)
        if root not in EXPECTED_TOP_KEYS:
            raise PendingInterviewError(f"Ruta no permitida: {p}")


def _validate_append_path(path: str) -> None:
    root = _path_root(path)
    if root not in LIST_APPEND_ROOTS:
        raise PendingInterviewError(
            f"append solo en listas: {', '.join(sorted(LIST_APPEND_ROOTS))}"
        )


def validate_pending(doc: Any, cv_id: int | None = None) -> dict[str, Any]:
    if not isinstance(doc, dict):
        raise PendingInterviewError("pending debe ser un objeto JSON")
    if doc.get("version") != 1:
        raise PendingInterviewError("pending.version debe ser 1")
    q = (doc.get("question_markdown") or "").strip()
    if not q:
        raise PendingInterviewError("question_markdown vacío")
    inputs = doc.get("inputs")
    if not isinstance(inputs, list):
        raise PendingInterviewError("inputs debe ser una lista")
    for i, item in enumerate(inputs):
        if not isinstance(item, dict):
            raise PendingInterviewError(f"inputs[{i}] inválido")
        if not (item.get("name") or "").strip():
            raise PendingInterviewError(f"inputs[{i}].name obligatorio")
        item.setdefault("type", "textarea")
        item.setdefault("label", item["name"])
        item.setdefault("required", False)
        if item["type"] not in ("text", "textarea"):
            raise PendingInterviewError(f'inputs[{i}].type debe ser "text" o "textarea"')
    merge = doc.get("merge")
    if not isinstance(merge, dict):
        raise PendingInterviewError("merge debe ser objeto")
    mtype = (merge.get("type") or "").strip()
    if mtype not in ("assign_paths", "append_list_object", "append_list_string"):
        raise PendingInterviewError(f"merge.type desconocido: {mtype}")

    pcv = doc.get("cv_id")
    if pcv is not None and cv_id is not None:
        try:
            if int(pcv) != int(cv_id):
                raise PendingInterviewError(
                    f"Este pending es para el CV {pcv}; estás editando el CV {cv_id}"
                )
        except (TypeError, ValueError) as e:
            raise PendingInterviewError("cv_id en pending debe ser un entero") from e

    if mtype == "assign_paths":
        assigns = merge.get("assignments")
        if not isinstance(assigns, list) or not assigns:
            raise PendingInterviewError("assign_paths requiere merge.assignments[]")
        paths: list[str] = []
        for j, a in enumerate(assigns):
            if not isinstance(a, dict):
                raise PendingInterviewError(f"assignments[{j}] inválido")
            inp = (a.get("input") or "").strip()
            path = (a.get("path") or "").strip()
            if not inp:
                raise PendingInterviewError(f"assignments[{j}].input obligatorio")
            if not path:
                raise PendingInterviewError(f"assignments[{j}].path obligatorio")
            paths.append(path)
        _validate_path_roots(paths)
    elif mtype == "append_list_object":
        path = (merge.get("path") or "").strip()
        if not path:
            raise PendingInterviewError("append_list_object requiere merge.path")
        mapping = merge.get("mapping")
        if not isinstance(mapping, dict) or not mapping:
            raise PendingInterviewError("append_list_object requiere merge.mapping")
        _validate_append_path(path)
    else:
        path = (merge.get("path") or "").strip()
        if not path:
            raise PendingInterviewError("append_list_string requiere merge.path")
        _validate_append_path(path)

    return doc


def read_pending_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise PendingInterviewError(f"No se pudo leer pending: {e}") from e


def question_html(markdown_text: str) -> str:
    return md_lib.markdown(
        markdown_text,
        extensions=["extra", "nl2br", "sane_lists"],
    )


class _SafeFormat(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _format_review(template: str, answers: dict[str, str]) -> str:
    safe = _SafeFormat(**{k: (v if v is not None else "") for k, v in answers.items()})
    try:
        return template.format_map(safe)
    except (ValueError, KeyError):
        return template


def _set_dotted(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur: Any = data
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def _get_dotted_container(
    data: dict[str, Any], path: str
) -> tuple[dict[str, Any], str]:
    parts = path.split(".")
    cur: Any = data
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    return cur, parts[-1]


def collect_answers(pending: dict[str, Any], form: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    for spec in pending["inputs"]:
        name = spec["name"].strip()
        raw = form.get(name) or ""
        if spec.get("type") == "text":
            val = raw.strip()
        else:
            val = str(raw).rstrip()
        req = bool(spec.get("required"))
        if req and not val:
            raise PendingInterviewError(f"Campo obligatorio: {spec.get('label') or name}")
        out[name] = val
    return out


def apply_merge(
    data: dict[str, Any],
    pending: dict[str, Any],
    answers: dict[str, str],
) -> dict[str, Any]:
    data = deepcopy(data)
    validate_context_shape(data)
    merge = pending["merge"]
    mtype = merge["type"]

    if mtype == "assign_paths":
        for a in merge["assignments"]:
            inp = a["input"]
            path = (a["path"] or "").strip()
            if inp in answers and path:
                _set_dotted(data, path, answers[inp])

    elif mtype == "append_list_object":
        path = (merge["path"] or "").strip()
        mapping = merge["mapping"]
        defaults = merge.get("defaults") or {}
        if not isinstance(defaults, dict):
            defaults = {}
        obj: dict[str, Any] = {**defaults}
        for form_key, obj_key in mapping.items():
            if isinstance(obj_key, str):
                obj[obj_key] = answers.get(form_key, "")
        parent, key = _get_dotted_container(data, path)
        lst = parent.get(key)
        if not isinstance(lst, list):
            lst = []
        lst.append(obj)
        parent[key] = lst

    elif mtype == "append_list_string":
        path = (merge["path"] or "").strip()
        input_name = merge.get("input")
        if not input_name:
            first = pending["inputs"][0]["name"] if pending["inputs"] else None
            input_name = first
        text = (answers.get(input_name or "", "") or "").strip()
        if not text:
            validate_context_shape(data)
            return data
        parent, key = _get_dotted_container(data, path)
        lst = parent.get(key)
        if not isinstance(lst, list):
            lst = []
        lst.append(text)
        parent[key] = lst

    validate_context_shape(data)
    return data


def append_to_review(
    current: str | None,
    pending: dict[str, Any],
    answers: dict[str, str],
) -> str:
    block = (pending.get("review_append") or {}).get("markdown")
    qh = (pending.get("review_heading") or "").strip()
    if block:
        piece = _format_review(block, answers).strip()
    else:
        q_plain = re.sub(r"[#*_`\[\]]", "", pending["question_markdown"])
        q_short = " ".join(q_plain.split())[:240]
        piece = f"## Ronda\n*{q_short}*\n\n"
        for k, v in answers.items():
            if v.strip():
                piece += f"**{k}:** {v.strip()}\n\n"
    parts = [current.strip() if current else "", piece]
    return "\n\n".join(p for p in parts if p).strip() + "\n"


def write_review_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def remove_pending_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def seed_pending_from_template(path: Path, cv_id: int) -> dict[str, Any]:
    """
    Crea cv-interview.pending.json copiando la plantilla del repo y fijando cv_id.
    Útil cuando aún no hay MCP o quien entrevista quiere arrancar la primera ronda en local.
    """
    tpl = pending_template_path()
    try:
        with tpl.open(encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise PendingInterviewError(f"No se pudo leer la plantilla: {e}") from e
    if not isinstance(doc, dict):
        raise PendingInterviewError("La plantilla debe ser un objeto JSON")
    doc = deepcopy(doc)
    doc["cv_id"] = int(cv_id)
    validate_pending(doc, cv_id=cv_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return doc
