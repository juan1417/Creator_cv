"""Flask routes: exponen los use cases como endpoints HTTP.

Cada endpoint:
1. Extrae el user_id del JWT (vía middleware)
2. Parsea el input
3. Llama al use case
4. Devuelve la respuesta JSON
"""
from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import Blueprint, Flask, g, jsonify, request

from ...application.dto import (
    ChatMessageRequest,
    CreateCVRequest,
    UpdateCVRequest,
)
from ...application.inputs import (
    CreateCVInput,
    DeleteCVInput,
    GetCVInput,
    UpdateCVInput,
)
from ...application.use_cases import (
    AppendChat,
    ClearChat,
    CreateCV,
    DeleteCV,
    GetCV,
    GetChat,
    ListCVs,
    UpdateCV,
)
from ...domain.exceptions import UnauthorizedError


api = Blueprint("api", __name__, url_prefix="/api")


# ── Middleware: extraer user_id del JWT ───────────────────────────────────
def require_auth(auth_verifier) -> Callable:
    """Decorator: extrae el Bearer token, lo verifica y guarda user_id en g."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                raise UnauthorizedError("Falta el header Authorization")
            user_id = auth_verifier.verify(auth_header)
            g.user_id = user_id
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def register_routes(
    app: Flask,
    *,
    create_cv: CreateCV,
    get_cv: GetCV,
    list_cvs: ListCVs,
    update_cv: UpdateCV,
    delete_cv: DeleteCV,
    get_chat: GetChat,
    append_chat: AppendChat,
    clear_chat: ClearChat,
    auth_verifier,
) -> None:
    @api.get("/health")
    def health():
        return jsonify({"ok": True, "service": "creator-cv-backend"}), 200

    # ── CVs ────────────────────────────────────────────────────────────
    @api.get("/cvs")
    @require_auth(auth_verifier)
    def list_cvs_route():
        cvs = list_cvs.execute(g.user_id, ListCVsInput())
        return jsonify({"ok": True, "cvs": [c.model_dump(mode="json") for c in cvs]}), 200

    @api.post("/cvs")
    @require_auth(auth_verifier)
    def create_cv_route():
        body = CreateCVRequest.model_validate(request.get_json(silent=True) or {})
        result = create_cv.execute(
            g.user_id,
            CreateCVInput(title=body.title, context_json=body.context_json),
        )
        return jsonify({"ok": True, "cv": result.model_dump(mode="json")}), 201

    @api.get("/cvs/<cv_id>")
    @require_auth(auth_verifier)
    def get_cv_route(cv_id: str):
        result = get_cv.execute(g.user_id, GetCVInput(cv_id=cv_id))
        return jsonify({"ok": True, "cv": result.model_dump(mode="json")}), 200

    @api.put("/cvs/<cv_id>")
    @api.patch("/cvs/<cv_id>")
    @require_auth(auth_verifier)
    def update_cv_route(cv_id: str):
        body = UpdateCVRequest.model_validate(request.get_json(silent=True) or {})
        result = update_cv.execute(
            g.user_id,
            UpdateCVInput(
                cv_id=cv_id, title=body.title, context_json=body.context_json
            ),
        )
        return jsonify({"ok": True, "cv": result.model_dump(mode="json")}), 200

    @api.delete("/cvs/<cv_id>")
    @require_auth(auth_verifier)
    def delete_cv_route(cv_id: str):
        delete_cv.execute(g.user_id, DeleteCVInput(cv_id=cv_id))
        return jsonify({"ok": True}), 200

    # ── Chat ───────────────────────────────────────────────────────────
    @api.get("/cvs/<cv_id>/chat")
    @require_auth(auth_verifier)
    def get_chat_route(cv_id: str):
        # verifica que el CV existe y pertenece al user
        get_cv.execute(g.user_id, GetCVInput(cv_id=cv_id))
        msgs = get_chat.execute(g.user_id, cv_id)
        return jsonify(
            {
                "ok": True,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "patch": m.patch,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in msgs
                ],
            }
        ), 200

    @api.post("/cvs/<cv_id>/chat")
    @require_auth(auth_verifier)
    def append_chat_route(cv_id: str):
        body = ChatMessageRequest.model_validate(request.get_json(silent=True) or {})
        # verifica que el CV existe y pertenece al user
        get_cv.execute(g.user_id, GetCVInput(cv_id=cv_id))
        msg = append_chat.execute(
            g.user_id, cv_id, body.role, body.content, body.patch
        )
        return jsonify({"ok": True, "count": None, "message": {
            "role": msg.role,
            "content": msg.content,
            "patch": msg.patch,
            "created_at": msg.created_at.isoformat(),
        }}), 201

    @api.delete("/cvs/<cv_id>/chat")
    @require_auth(auth_verifier)
    def clear_chat_route(cv_id: str):
        get_cv.execute(g.user_id, GetCVInput(cv_id=cv_id))
        clear_chat.execute(g.user_id, cv_id)
        return jsonify({"ok": True}), 200

    app.register_blueprint(api)
