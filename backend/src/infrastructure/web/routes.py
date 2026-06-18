from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Blueprint, Flask, g, jsonify, request
from sqlalchemy import select

from ...application.dto import (
    ChatMessageRequest,
    CreateCVRequest,
    LoginRequest,
    RegisterRequest,
    UpdateCVRequest,
)
from ...application.inputs import (
    CreateCVInput,
    DeleteCVInput,
    GetCVInput,
    ListCVsInput,
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
from ..auth.local_auth import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from ..persistence.models import UserModel


def make_require_auth(auth_verifier: Callable[[str], str]) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                raise UnauthorizedError("Falta el header Authorization")
            user_id = auth_verifier(auth_header)
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
    auth_verifier: Callable[[str], str],
    get_session_factory: Callable,
) -> None:
    require_auth = make_require_auth(auth_verifier)

    api = Blueprint("api", __name__, url_prefix="/api")

    # ── Health ────────────────────────────────────────────────────────
    @api.get("/health")
    def health():
        return jsonify({"ok": True, "service": "creator-cv-backend"}), 200

    # ── Auth ──────────────────────────────────────────────────────────
    @api.post("/auth/register")
    def register():
        body = RegisterRequest.model_validate(request.get_json(silent=True) or {})
        with get_session_factory() as session:
            existing = session.scalar(
                select(UserModel).where(UserModel.email == body.email)
            )
            if existing:
                return jsonify({"ok": False, "error": "El email ya está registrado"}), 409
            user = UserModel(
                email=body.email,
                password_hash=hash_password(body.password),
            )
            session.add(user)
            session.flush()
            token = create_token(user.id, user.email)
            return jsonify({"ok": True, "token": token, "user_id": user.id, "email": user.email}), 201

    @api.post("/auth/login")
    def login():
        body = LoginRequest.model_validate(request.get_json(silent=True) or {})
        with get_session_factory() as session:
            user = session.scalar(
                select(UserModel).where(UserModel.email == body.email)
            )
            if not user or not verify_password(body.password, user.password_hash):
                return jsonify({"ok": False, "error": "Email o contraseña incorrectos"}), 401
            token = create_token(user.id, user.email)
            return jsonify({"ok": True, "token": token, "user_id": user.id, "email": user.email}), 200

    @api.get("/auth/me")
    @require_auth
    def me():
        payload = decode_token(request.headers.get("Authorization", ""))
        return jsonify({"ok": True, "user_id": g.user_id, "email": payload.get("email")}), 200

    # ── CVs ───────────────────────────────────────────────────────────
    @api.get("/cvs")
    @require_auth
    def list_cvs_route():
        cvs = list_cvs.execute(g.user_id, ListCVsInput())
        return jsonify({"ok": True, "cvs": [c.model_dump(mode="json") for c in cvs]}), 200

    @api.post("/cvs")
    @require_auth
    def create_cv_route():
        body = CreateCVRequest.model_validate(request.get_json(silent=True) or {})
        result = create_cv.execute(
            g.user_id,
            CreateCVInput(title=body.title, context_json=body.context_json),
        )
        return jsonify({"ok": True, "cv": result.model_dump(mode="json")}), 201

    @api.get("/cvs/<cv_id>")
    @require_auth
    def get_cv_route(cv_id: str):
        result = get_cv.execute(g.user_id, GetCVInput(cv_id=cv_id))
        return jsonify({"ok": True, "cv": result.model_dump(mode="json")}), 200

    @api.put("/cvs/<cv_id>")
    @api.patch("/cvs/<cv_id>")
    @require_auth
    def update_cv_route(cv_id: str):
        body = UpdateCVRequest.model_validate(request.get_json(silent=True) or {})
        result = update_cv.execute(
            g.user_id,
            UpdateCVInput(cv_id=cv_id, title=body.title, context_json=body.context_json),
        )
        return jsonify({"ok": True, "cv": result.model_dump(mode="json")}), 200

    @api.delete("/cvs/<cv_id>")
    @require_auth
    def delete_cv_route(cv_id: str):
        delete_cv.execute(g.user_id, DeleteCVInput(cv_id=cv_id))
        return jsonify({"ok": True}), 200

    # ── Chat ──────────────────────────────────────────────────────────
    @api.get("/cvs/<cv_id>/chat")
    @require_auth
    def get_chat_route(cv_id: str):
        get_cv.execute(g.user_id, GetCVInput(cv_id=cv_id))
        msgs = get_chat.execute(g.user_id, cv_id)
        return jsonify({
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
        }), 200

    @api.post("/cvs/<cv_id>/chat")
    @require_auth
    def append_chat_route(cv_id: str):
        body = ChatMessageRequest.model_validate(request.get_json(silent=True) or {})
        get_cv.execute(g.user_id, GetCVInput(cv_id=cv_id))
        msg = append_chat.execute(g.user_id, cv_id, body.role, body.content, body.patch)
        return jsonify({
            "ok": True,
            "count": None,
            "message": {
                "role": msg.role,
                "content": msg.content,
                "patch": msg.patch,
                "created_at": msg.created_at.isoformat(),
            },
        }), 201

    @api.delete("/cvs/<cv_id>/chat")
    @require_auth
    def clear_chat_route(cv_id: str):
        get_cv.execute(g.user_id, GetCVInput(cv_id=cv_id))
        clear_chat.execute(g.user_id, cv_id)
        return jsonify({"ok": True}), 200

    app.register_blueprint(api)
