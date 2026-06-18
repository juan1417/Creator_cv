"""
API REST para que el frontend estático se sincronice con el backend.

Endpoints (todos devuelven JSON):
    GET    /api/cvs                  → listar CVs del usuario
    POST   /api/cvs                  → crear nuevo CV
    GET    /api/cvs/<id>             → obtener un CV
    PUT    /api/cvs/<id>             → actualizar (reemplazar context_json)
    DELETE /api/cvs/<id>             → eliminar
    GET    /api/cvs/<id>/chat        → historial de chat
    POST   /api/cvs/<id>/chat        → append mensaje
    DELETE /api/cvs/<id>/chat        → vaciar historial
    POST   /api/gemini               → chat con Gemini (proxy)
    GET    /api/health               → health check

Auth: deshabilitada por ahora (single-user, dev@local). Para multi-user,
agregar token en Authorization header.
"""
from __future__ import annotations

import json
import os
from typing import Any

from flask import Blueprint, abort, jsonify, request

from creator_cv.context_sync import (
    EXPECTED_TOP_KEYS,
    parse_cv_context_json,
    validate_context_shape,
)
from creator_cv.extensions import csrf, db
from creator_cv.models import CV, User

bp = Blueprint("api", __name__, url_prefix="/api")


# ── Helpers ────────────────────────────────────────────────────────────────
def _get_dev_user() -> User:
    user = User.query.filter_by(email="dev@local").first()
    if not user:
        user = User(email="dev@local")
        db.session.add(user)
        db.session.commit()
    return user


def _cv_to_dict(cv: CV) -> dict[str, Any]:
    return {
        "id": cv.id,
        "title": cv.title,
        "context_json": cv.context_json,
        "created_at": cv.created_at.isoformat() if cv.created_at else None,
        "updated_at": cv.updated_at.isoformat() if cv.updated_at else None,
    }


def _parse_context(cv: CV) -> dict[str, Any]:
    try:
        return parse_cv_context_json(cv.context_json)
    except (json.JSONDecodeError, ValueError):
        return {}


# CSRF: la API usa JSON y Authorization (no cookies de sesión),
# así que exceptuamos todo /api/* del CSRF check.
csrf.exempt(bp)


# ── Health ─────────────────────────────────────────────────────────────────
@bp.get("/health")
def health():
    return jsonify({"ok": True, "service": "creator-cv-api"}), 200


# ── CRUD de CVs ────────────────────────────────────────────────────────────
@bp.get("/cvs")
def list_cvs():
    user = _get_dev_user()
    cvs = CV.query.filter_by(user_id=user.id).order_by(CV.updated_at.desc()).all()
    return jsonify({"ok": True, "cvs": [_cv_to_dict(c) for c in cvs]}), 200


@bp.post("/cvs")
def create_cv():
    user = _get_dev_user()
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip() or "Sin título"
    context_json = body.get("context_json")
    if context_json is None:
        from creator_cv.cv_render import json_to_markdown  # noqa
        # Estructura vacía con todas las claves
        empty = {
            "meta": {
                "nombre_completo": "", "titulo_profesional": "",
                "idioma_cv": "español", "objetivo_cv": "",
                "tipo_cv": "", "nivel_seniority": "",
                "contacto": {"telefono": "", "email": "", "linkedin": "", "ubicacion": ""},
            },
            "certificaciones": [], "fortalezas": [],
            "perfil_profesional": {"resumen": "", "palabras_clave": []},
            "experiencia": [], "educacion": [],
            "habilidades": {"tecnicas": [], "blandas": [], "idiomas": []},
            "proyectos": [],
            "recursos_actuales": {"cv_existente": False, "texto_cv": "", "links": []},
            "restricciones": {"extension_maxima_paginas": 1, "formato_solicitado": "PDF", "otro": ""},
            "dudas_pendientes": [],
        }
        context_json = json.dumps(empty, ensure_ascii=False, indent=2)
    cv = CV(user_id=user.id, title=title, context_json=context_json)
    db.session.add(cv)
    db.session.commit()
    return jsonify({"ok": True, "cv": _cv_to_dict(cv)}), 201


@bp.get("/cvs/<int:cv_id>")
def get_cv(cv_id: int):
    user = _get_dev_user()
    cv = CV.query.filter_by(id=cv_id, user_id=user.id).first()
    if not cv:
        return jsonify({"ok": False, "error": "CV no encontrado"}), 404
    return jsonify({"ok": True, "cv": _cv_to_dict(cv)}), 200


@bp.put("/cvs/<int:cv_id>")
@bp.patch("/cvs/<int:cv_id>")
def update_cv(cv_id: int):
    user = _get_dev_user()
    cv = CV.query.filter_by(id=cv_id, user_id=user.id).first()
    if not cv:
        return jsonify({"ok": False, "error": "CV no encontrado"}), 404
    body = request.get_json(silent=True) or {}
    if "title" in body:
        new_title = (body.get("title") or "").strip()
        if new_title:
            cv.title = new_title
    if "context_json" in body:
        ctx_raw = body["context_json"]
        if isinstance(ctx_raw, (dict, list)):
            ctx_raw = json.dumps(ctx_raw, ensure_ascii=False, indent=2)
        # Validar JSON y shape mínimo
        try:
            parsed = json.loads(ctx_raw)
        except json.JSONDecodeError as e:
            return jsonify({"ok": False, "error": f"JSON inválido: {e}"}), 400
        if not isinstance(parsed, dict):
            return jsonify({"ok": False, "error": "context_json debe ser un objeto JSON"}), 400
        cv.context_json = json.dumps(parsed, ensure_ascii=False, indent=2)
    db.session.commit()
    return jsonify({"ok": True, "cv": _cv_to_dict(cv)}), 200


@bp.delete("/cvs/<int:cv_id>")
def delete_cv(cv_id: int):
    user = _get_dev_user()
    cv = CV.query.filter_by(id=cv_id, user_id=user.id).first()
    if not cv:
        return jsonify({"ok": False, "error": "CV no encontrado"}), 404
    db.session.delete(cv)
    db.session.commit()
    return jsonify({"ok": True}), 200


# ── Chat (historial) ───────────────────────────────────────────────────────
@bp.get("/cvs/<int:cv_id>/chat")
def get_chat(cv_id: int):
    user = _get_dev_user()
    cv = CV.query.filter_by(id=cv_id, user_id=user.id).first()
    if not cv:
        return jsonify({"ok": False, "error": "CV no encontrado"}), 404
    history = []
    if cv.chat_history_json:
        try:
            history = json.loads(cv.chat_history_json)
        except json.JSONDecodeError:
            history = []
    return jsonify({"ok": True, "messages": history}), 200


@bp.post("/cvs/<int:cv_id>/chat")
def append_chat(cv_id: int):
    user = _get_dev_user()
    cv = CV.query.filter_by(id=cv_id, user_id=user.id).first()
    if not cv:
        return jsonify({"ok": False, "error": "CV no encontrado"}), 404
    body = request.get_json(silent=True) or {}
    messages = body.get("messages")
    if not isinstance(messages, list):
        return jsonify({"ok": False, "error": "messages debe ser una lista"}), 400
    cv.chat_history_json = json.dumps(messages, ensure_ascii=False)
    db.session.commit()
    return jsonify({"ok": True, "count": len(messages)}), 200


@bp.delete("/cvs/<int:cv_id>/chat")
def clear_chat(cv_id: int):
    user = _get_dev_user()
    cv = CV.query.filter_by(id=cv_id, user_id=user.id).first()
    if not cv:
        return jsonify({"ok": False, "error": "CV no encontrado"}), 404
    cv.chat_history_json = "[]"
    db.session.commit()
    return jsonify({"ok": True}), 200


# ── Gemini (proxy server-side) ─────────────────────────────────────────────
@bp.post("/gemini")
def gemini_proxy():
    """Proxy a Google Gemini. Mantiene GEMINI_API_KEY en el servidor."""
    from creator_cv.gemini_chat import generate_response  # type: ignore

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"ok": False, "error": "Falta GEMINI_API_KEY en el servidor"}), 500
    body = request.get_json(silent=True) or {}
    messages = body.get("messages") or []
    capacity = body.get("user_capacity", "intermedio")
    cv_context = body.get("cv_context") or {}
    try:
        result = generate_response(
            api_key=api_key,
            messages=messages,
            user_capacity=capacity,
            cv_context=cv_context,
        )
        return jsonify({"ok": True, **result}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
