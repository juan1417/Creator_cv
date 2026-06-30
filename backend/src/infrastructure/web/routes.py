from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Blueprint, Flask, g, jsonify, request

from ...application.dto import (
    ChatMessageRequest,
    CompareRequest,
    CreateCVRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RegenerateBackupCodesRequest,
    ResetPasswordRequest,
    ResendVerificationRequest,
    TwoFactorDisableRequest,
    TwoFactorSetupConfirmRequest,
    TwoFactorVerifyRequest,
    UpdateCVRequest,
    VerifyEmailRequest,
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
    DisableTotp,
    DuplicateCV,
    ForgotPassword,
    GetCV,
    GetChat,
    ListCVs,
    LoginPending,
    LoginUser,
    Logout,
    RefreshSession,
    RegenerateBackupCodes,
    RegisterUser,
    ResendVerification,
    ResetPassword,
    SetupTotpConfirm,
    SetupTotpStart,
    UpdateCV,
    VerifyEmail,
    VerifyTwoFactor,
)
from ...domain.exceptions import UnauthorizedError
from ..auth.local_auth import decode_token
from .limiter import get_email_key, get_login_key, limiter


def _session_payload(session) -> dict[str, Any]:
    return {
        "ok": True,
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "user_id": session.user_id,
        "email": session.email,
    }


def _login_outcome_payload(outcome) -> dict[str, Any]:
    """Serializa AuthSession (normal) o LoginPending (2FA)."""
    if isinstance(outcome, LoginPending):
        return {
            "ok": True,
            "requires_2fa": True,
            "pending_token": outcome.pending_token,
            "user_id": outcome.user_id,
            "email": outcome.email,
        }
    return _session_payload(outcome)


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
    # CV / chat
    create_cv: CreateCV,
    get_cv: GetCV,
    list_cvs: ListCVs,
    update_cv: UpdateCV,
    delete_cv: DeleteCV,
    duplicate_cv: DuplicateCV,
    get_chat: GetChat,
    append_chat: AppendChat,
    clear_chat: ClearChat,
    # Compare
    compare_cv=None,
    # History
    get_cv_history=None,
    restore_snapshot=None,
    # Auth
    register_user: RegisterUser,
    login_user: LoginUser,
    verify_email_uc: VerifyEmail,
    resend_verification_uc: ResendVerification,
    forgot_password_uc: ForgotPassword,
    reset_password_uc: ResetPassword,
    refresh_session_uc: RefreshSession,
    logout_uc: Logout,
    # 2FA
    verify_two_factor_uc: VerifyTwoFactor,
    setup_totp_start_uc: SetupTotpStart,
    setup_totp_confirm_uc: SetupTotpConfirm,
    disable_totp_uc: DisableTotp,
    regenerate_backup_codes_uc: RegenerateBackupCodes,
    # Misc
    auth_verifier: Callable[[str], str],
) -> None:
    require_auth = make_require_auth(auth_verifier)

    api = Blueprint("api", __name__, url_prefix="/api")

    # ── Health ────────────────────────────────────────────────────────
    @api.get("/health")
    def health():
        return jsonify({"ok": True, "service": "creator-cv-backend"}), 200

    # ── Auth: registro y login ────────────────────────────────────────

    @api.post("/auth/register")
    @limiter.limit("5 per hour")
    def register():
        body = RegisterRequest.model_validate(request.get_json(silent=True) or {})
        result = register_user.execute(
            email=str(body.email),
            password=body.password,
            password_hasher=_password_hasher,
        )
        payload: dict[str, Any] = {
            "ok": True,
            "user_id": result.user_id,
            "email": result.email,
            "requires_verification": result.requires_verification,
        }
        if not result.requires_verification:
            from ...application.use_cases import _issue_auth_session
            user = _find_user(result.user_id)
            session, _ = _issue_auth_session(
                user, _refresh_repo_instance, _token_creator
            )
            payload.update({
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
            })
        return jsonify(payload), 201

    @api.post("/auth/login")
    @limiter.limit("10 per 15 minutes", key_func=get_login_key)
    def login():
        body = LoginRequest.model_validate(request.get_json(silent=True) or {})
        outcome = login_user.execute(email=str(body.email), password=body.password)
        return jsonify(_login_outcome_payload(outcome)), 200

    # ── Auth: refresh tokens ──────────────────────────────────────────

    @api.post("/auth/refresh")
    @limiter.limit("60 per hour")
    def refresh_route():
        body = RefreshRequest.model_validate(request.get_json(silent=True) or {})
        session = refresh_session_uc.execute(body.refresh_token)
        return jsonify(_session_payload(session)), 200

    # ── Auth: verificación de email ───────────────────────────────────

    @api.post("/auth/verify-email")
    def verify_email_route():
        body = VerifyEmailRequest.model_validate(request.get_json(silent=True) or {})
        outcome = verify_email_uc.execute(body.token)
        return jsonify(_login_outcome_payload(outcome)), 200

    @api.post("/auth/resend-verification")
    @limiter.limit("3 per hour", key_func=get_email_key)
    def resend_verification_route():
        body = ResendVerificationRequest.model_validate(request.get_json(silent=True) or {})
        resend_verification_uc.execute(str(body.email))
        return jsonify({"ok": True}), 200

    # ── Auth: reset de contraseña ─────────────────────────────────────

    @api.post("/auth/forgot-password")
    @limiter.limit("3 per hour")
    def forgot_password_route():
        body = ForgotPasswordRequest.model_validate(request.get_json(silent=True) or {})
        forgot_password_uc.execute(str(body.email))
        return jsonify({"ok": True}), 200

    @api.post("/auth/reset-password")
    @limiter.limit("5 per hour")
    def reset_password_route():
        body = ResetPasswordRequest.model_validate(request.get_json(silent=True) or {})
        reset_password_uc.execute(body.token, body.new_password)
        return jsonify({"ok": True}), 200

    # ── Auth: sesión actual / logout ──────────────────────────────────

    @api.get("/auth/me")
    @require_auth
    def me():
        payload = decode_token(request.headers.get("Authorization", ""))
        return jsonify({"ok": True, "user_id": g.user_id, "email": payload.get("email")}), 200

    @api.post("/auth/logout")
    @require_auth
    def logout_route():
        body = LogoutRequest.model_validate(request.get_json(silent=True) or {})
        logout_uc.execute(body.refresh_token)
        return jsonify({"ok": True}), 200

    # ── 2FA / TOTP ─────────────────────────────────────────────────────

    @api.post("/auth/2fa/verify")
    @limiter.limit("10 per 15 minutes", key_func=get_login_key)
    def verify_two_factor_route():
        """Segundo paso del login: pending_token + code → sesión."""
        body = TwoFactorVerifyRequest.model_validate(request.get_json(silent=True) or {})
        session = verify_two_factor_uc.execute(body.pending_token, body.code)
        return jsonify(_session_payload(session)), 200

    @api.post("/auth/2fa/setup")
    @require_auth
    @limiter.limit("10 per hour")
    def setup_totp_start_route():
        """Inicia setup: genera secret + QR. NO habilita 2FA todavía."""
        result = setup_totp_start_uc.execute(g.user_id)
        return jsonify({
            "ok": True,
            "qr_data_url": result.qr_data_url,
            "manual_key": result.manual_key,
            "otpauth_uri": result.otpauth_uri,
        }), 200

    @api.post("/auth/2fa/verify-setup")
    @require_auth
    @limiter.limit("10 per hour")
    def setup_totp_confirm_route():
        """Confirma setup con un code del authenticator. Habilita 2FA + emite backup codes."""
        body = TwoFactorSetupConfirmRequest.model_validate(
            request.get_json(silent=True) or {}
        )
        result = setup_totp_confirm_uc.execute(g.user_id, body.code)
        return jsonify({
            "ok": True,
            "backup_codes": result.backup_codes,
        }), 200

    @api.post("/auth/2fa/disable")
    @require_auth
    @limiter.limit("5 per hour")
    def disable_totp_route():
        body = TwoFactorDisableRequest.model_validate(
            request.get_json(silent=True) or {}
        )
        disable_totp_uc.execute(g.user_id, body.password, body.code)
        return jsonify({"ok": True}), 200

    @api.post("/auth/2fa/backup-codes")
    @require_auth
    @limiter.limit("3 per hour")
    def regenerate_backup_codes_route():
        body = RegenerateBackupCodesRequest.model_validate(
            request.get_json(silent=True) or {}
        )
        codes = regenerate_backup_codes_uc.execute(g.user_id, body.password)
        return jsonify({"ok": True, "backup_codes": codes}), 200

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

    @api.route("/cvs/<cv_id>", methods=["PUT", "PATCH"])
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

    @api.post("/cvs/<cv_id>/duplicate")
    @require_auth
    def duplicate_cv_route(cv_id: str):
        """Crea una copia del CV con título ``"(Copia)"``. Mismo ``context_json``."""
        new_cv = duplicate_cv.execute(g.user_id, cv_id)
        return jsonify({"ok": True, "cv": new_cv.model_dump(mode="json")}), 201

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

    # ── Compare ───────────────────────────────────────────────────────
    @api.post("/compare")
    @require_auth
    def compare_route():
        if compare_cv is None:
            return jsonify({"error": "Comparador no disponible"}), 501
        body = CompareRequest.model_validate(request.get_json(silent=True) or {})
        cv = get_cv.execute(g.user_id, GetCVInput(cv_id=body.cv_id))
        result = compare_cv.execute(
            cv.context_json, body.job_title, body.job_description
        )
        return jsonify({
            "ok": True,
            "score": result.score,
            "verdict": result.verdict,
            "sub_scores": result.sub_scores,
            "improvements": result.improvements,
            "strengths": result.strengths,
            "gaps": result.gaps,
        }), 200

    # ── History ───────────────────────────────────────────────────────
    @api.get("/history")
    @require_auth
    def get_history_route():
        if get_cv_history is None:
            return jsonify({"ok": True, "entries": []}), 200
        cv_id_filter = request.args.get("cv_id")
        event_type_filter = request.args.get("event_type")
        entries = get_cv_history.execute(
            g.user_id, cv_id=cv_id_filter, event_type=event_type_filter
        )
        return jsonify({
            "ok": True,
            "entries": [
                {
                    "id": e.id,
                    "cv_id": e.cv_id,
                    "event_type": e.event_type,
                    "title": e.title,
                    "description": e.description,
                    "created_at": e.created_at,
                }
                for e in entries
            ],
        }), 200

    @api.post("/history/<entry_id>/restore")
    @require_auth
    def restore_history_route(entry_id: str):
        if restore_snapshot is None:
            return jsonify({"error": "Historial no disponible"}), 501
        snapshot = restore_snapshot.execute(g.user_id, entry_id)
        if snapshot is None:
            return jsonify({"error": "Entrada no encontrada o sin snapshot"}), 404
        return jsonify({"ok": True, "snapshot": snapshot}), 200

    app.register_blueprint(api)


# Callbacks inyectados en runtime desde app_factory.
_password_hasher: Callable[[str], str] = lambda p: p
_token_creator: Callable[[str, str], str] = lambda uid, em: ""
_refresh_repo_instance: Any = None
_user_repo_instance: Any = None


def _find_user(user_id: str):
    return _user_repo_instance.get_by_id(user_id)


def set_auth_callbacks(
    *,
    password_hasher: Callable[[str], str],
    token_creator: Callable[[str, str], str],
    user_repo: Any,
    refresh_repo: Any,
) -> None:
    global _password_hasher, _token_creator, _user_repo_instance, _refresh_repo_instance
    _password_hasher = password_hasher
    _token_creator = token_creator
    _user_repo_instance = user_repo
    _refresh_repo_instance = refresh_repo
