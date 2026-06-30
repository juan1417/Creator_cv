"""Use cases: lógica de aplicación.

Cada use case es una clase con un único método ``execute()``.
Las dependencias se inyectan por constructor (no globales).
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Sequence, Union

from ..domain.entities import (
    CV,
    BackupCode,
    ChatMessage,
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    TwoFactorPending,
    User,
)
from ..domain.exceptions import (
    CVNotFoundError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTwoFactorCodeError,
    RefreshTokenReuseDetectedError,
    TokenExpiredError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
    UserAlreadyExistsError,
    ValidationError,
)
from ..domain.repositories import (
    BackupCodeRepository,
    ChatRepository,
    CVRepository,
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    TwoFactorPendingRepository,
    UserRepository,
)
from ..infrastructure.auth.refresh_tokens import (
    generate_refresh_token,
    hash_refresh_token,
)
from ..infrastructure.auth.tokens import generate_token, hash_token
from ..infrastructure.email.sender import EmailSender
from ..infrastructure.email.templates import password_reset_email, verification_email
from .dto import CVResponse
from .inputs import (
    CreateCVInput,
    DeleteCVInput,
    GetCVInput,
    ListCVsInput,
    UpdateCVInput,
)

log = logging.getLogger(__name__)


# ── Helpers CV ────────────────────────────────────────────────────────────


def _cv_to_response(cv: CV) -> CVResponse:
    return CVResponse(
        id=cv.id,
        title=cv.title,
        context_json=cv.context_json,
        created_at=cv.created_at,
        updated_at=cv.updated_at,
    )


def _empty_context_json() -> str:
    return json.dumps(
        {
            "meta": {
                "nombre_completo": "",
                "titulo_profesional": "",
                "idioma_cv": "español",
                "objetivo_cv": "",
                "tipo_cv": "",
                "nivel_seniority": "",
                "contacto": {
                    "telefono": "",
                    "email": "",
                    "linkedin": "",
                    "ubicacion": "",
                },
            },
            "certificaciones": [],
            "fortalezas": [],
            "perfil_profesional": {"resumen": "", "palabras_clave": []},
            "experiencia": [],
            "educacion": [],
            "habilidades": {"tecnicas": [], "blandas": [], "idiomas": []},
            "proyectos": [],
            "recursos_actuales": {"cv_existente": False, "texto_cv": "", "links": []},
            "restricciones": {
                "extension_maxima_paginas": 1,
                "formato_solicitado": "PDF",
                "otro": "",
            },
            "dudas_pendientes": [],
        },
        ensure_ascii=False,
        indent=2,
    )


def _validate_context_json(raw: str) -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValidationError("context_json", f"JSON inválido: {e}")
    if not isinstance(data, dict):
        raise ValidationError("context_json", "Debe ser un objeto JSON de nivel superior")
    return json.dumps(data, ensure_ascii=False, indent=2)


# ── CV use cases ─────────────────────────────────────────────────────────


class CreateCV:
    def __init__(self, cv_repo: CVRepository, history_recorder=None) -> None:
        self._repo = cv_repo
        self._history_recorder = history_recorder

    def execute(self, user_id: str, input: CreateCVInput) -> CVResponse:
        context = input.context_json.strip() if input.context_json else ""
        if not context:
            context = _empty_context_json()
        else:
            context = _validate_context_json(context)

        now = datetime.utcnow()
        cv = CV(
            id="",
            user_id=user_id,
            title=input.title,
            context_json=context,
            created_at=now,
            updated_at=now,
        )
        saved = self._repo.create(cv)

        if self._history_recorder:
            try:
                self._history_recorder.execute(
                    user_id=user_id,
                    cv_id=saved.id,
                    event_type="created",
                    title="CV creado",
                    description=f"Se creó el CV \"{input.title}\"",
                )
            except Exception:
                log.exception("Failed to record history for CV creation")

        return _cv_to_response(saved)


class GetCV:
    def __init__(self, cv_repo: CVRepository) -> None:
        self._repo = cv_repo

    def execute(self, user_id: str, input: GetCVInput) -> CVResponse:
        cv = self._repo.get(input.cv_id, user_id)
        return _cv_to_response(cv)


class ListCVs:
    def __init__(self, cv_repo: CVRepository) -> None:
        self._repo = cv_repo

    def execute(self, user_id: str, input: ListCVsInput) -> Sequence[CVResponse]:
        cvs = self._repo.list_for_user(user_id)
        return [_cv_to_response(cv) for cv in cvs]


class UpdateCV:
    def __init__(self, cv_repo: CVRepository, history_recorder=None) -> None:
        self._repo = cv_repo
        self._history_recorder = history_recorder

    def execute(self, user_id: str, input: UpdateCVInput) -> CVResponse:
        if input.title is None and input.context_json is None:
            raise ValidationError("body", "Debe enviar al menos title o context_json")

        cv = self._repo.get(input.cv_id, user_id)

        # Snapshot before changes (for history)
        snapshot_before = None
        if self._history_recorder and input.context_json is not None:
            try:
                snapshot_before = json.loads(cv.context_json) if cv.context_json else None
            except (json.JSONDecodeError, TypeError):
                snapshot_before = None

        if input.title is not None:
            cv.update_title(input.title)
        if input.context_json is not None:
            normalized = _validate_context_json(input.context_json)
            cv.update_context(normalized)
        updated = self._repo.update(cv)

        if self._history_recorder:
            try:
                changes = []
                if input.title is not None:
                    changes.append("título")
                if input.context_json is not None:
                    changes.append("contenido")
                desc = f"Se actualizó {', '.join(changes)} del CV"
                self._history_recorder.execute(
                    user_id=user_id,
                    cv_id=input.cv_id,
                    event_type="edited",
                    title="CV editado",
                    description=desc,
                    snapshot=snapshot_before,
                )
            except Exception:
                log.exception("Failed to record history for CV update")

        return _cv_to_response(updated)


class DeleteCV:
    def __init__(self, cv_repo: CVRepository) -> None:
        self._repo = cv_repo

    def execute(self, user_id: str, input: DeleteCVInput) -> None:
        self._repo.delete(input.cv_id, user_id)


class DuplicateCV:
    """Crea una copia de un CV existente con título ``"(Copia)"``.

    No incluye chat history ni nada específico del CV original — sólo el
    ``context_json``. Útil como punto de partida para una variación.
    """

    def __init__(self, cv_repo: CVRepository, history_recorder=None) -> None:
        self._repo = cv_repo
        self._history_recorder = history_recorder

    def execute(self, user_id: str, cv_id: str) -> CVResponse:
        source = self._repo.get(cv_id, user_id)  # raises CVNotFoundError si no existe
        now = datetime.utcnow()
        new_cv = CV(
            id="",
            user_id=user_id,
            title=f"{source.title} (Copia)",
            context_json=source.context_json,
            created_at=now,
            updated_at=now,
        )
        saved = self._repo.create(new_cv)

        if self._history_recorder:
            try:
                self._history_recorder.execute(
                    user_id=user_id,
                    cv_id=saved.id,
                    event_type="duplicated",
                    title="CV duplicado",
                    description=f"Copia de \"{source.title}\"",
                )
            except Exception:
                log.exception("Failed to record history for CV duplication")

        return _cv_to_response(saved)


class GetChat:
    def __init__(self, chat_repo: ChatRepository) -> None:
        self._repo = chat_repo

    def execute(self, user_id: str, cv_id: str) -> list[ChatMessage]:
        return self._repo.get_messages(cv_id, user_id)


class AppendChat:
    def __init__(self, chat_repo: ChatRepository) -> None:
        self._repo = chat_repo

    def execute(
        self, user_id: str, cv_id: str, role: str, content: str, patch: dict | None
    ) -> ChatMessage:
        msg = ChatMessage(role=role, content=content, patch=patch)
        self._repo.append(cv_id, user_id, msg)
        return msg


class ClearChat:
    def __init__(self, chat_repo: ChatRepository) -> None:
        self._repo = chat_repo

    def execute(self, user_id: str, cv_id: str) -> None:
        self._repo.clear(cv_id, user_id)


# ── Auth: sesión ─────────────────────────────────────────────────────────


@dataclass
class AuthSession:
    """Resultado de un login/refresh/verify exitoso."""

    user_id: str
    email: str
    access_token: str
    refresh_token: str


@dataclass
class LoginPending:
    """Resultado de un login que requiere segundo paso (2FA habilitado)."""

    user_id: str
    email: str
    pending_token: str  # se canjea en /api/auth/2fa/verify


# Union que LoginUser/VerifyEmail pueden devolver
LoginOutcome = Union[AuthSession, LoginPending]


def _issue_auth_session(
    user: User,
    refresh_repo: RefreshTokenRepository,
    access_token_creator: Callable[[str, str], str],
    *,
    refresh_ttl_days: int = 30,
) -> AuthSession:
    """Emite par access+refresh con una NUEVA family."""
    access = access_token_creator(user.id, user.email)
    raw_refresh = generate_refresh_token()
    now = datetime.now(timezone.utc)
    refresh = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        family_id=str(uuid.uuid4()),
        expires_at=now + timedelta(days=refresh_ttl_days),
        created_at=now,
    )
    refresh_repo.create(refresh)
    return AuthSession(
        user_id=user.id,
        email=user.email,
        access_token=access,
        refresh_token=raw_refresh,
    )


def _issue_2fa_pending(
    user: User,
    pending_repo: TwoFactorPendingRepository,
    *,
    pending_ttl_minutes: int = 5,
) -> LoginPending:
    """Emite un pending token (5 min) para el segundo paso del login."""
    from ..infrastructure.auth.tokens import generate_token as gen

    raw = gen()
    now = datetime.now(timezone.utc)
    pending = TwoFactorPending(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=now + timedelta(minutes=pending_ttl_minutes),
        created_at=now,
    )
    pending_repo.create(pending)
    return LoginPending(user_id=user.id, email=user.email, pending_token=raw)


# ── Auth use cases ───────────────────────────────────────────────────────


@dataclass
class RegisterUserOutput:
    user_id: str
    email: str
    requires_verification: bool


class RegisterUser:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: EmailVerificationTokenRepository,
        email_sender: EmailSender,
        *,
        frontend_url: str,
        skip_verification: bool = False,
        token_ttl_hours: int = 24,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._email_sender = email_sender
        self._frontend_url = frontend_url.rstrip("/")
        self._skip_verification = skip_verification
        self._token_ttl_hours = token_ttl_hours

    def execute(self, email: str, password: str, password_hasher: Callable[[str], str]) -> RegisterUserOutput:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise ValidationError("email", "Email requerido")

        existing = self._user_repo.get_by_email(normalized_email)
        if existing is not None:
            raise UserAlreadyExistsError(normalized_email)

        now = datetime.now(timezone.utc)
        user = User(
            id=str(uuid.uuid4()),
            email=normalized_email,
            password_hash=password_hasher(password),
            email_verified=self._skip_verification,
            email_verified_at=now if self._skip_verification else None,
            created_at=now,
        )
        user = self._user_repo.create(user)

        if self._skip_verification:
            return RegisterUserOutput(
                user_id=user.id, email=user.email, requires_verification=False
            )

        raw = generate_token()
        token = EmailVerificationToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=now + timedelta(hours=self._token_ttl_hours),
            created_at=now,
        )
        self._token_repo.create(token)

        verify_url = f"{self._frontend_url}/verify-email?token={raw}"
        subject, html, text = verification_email(
            verify_url=verify_url, frontend_url=self._frontend_url
        )
        try:
            self._email_sender.send(to=user.email, subject=subject, html=html, text=text)
        except Exception:
            log.exception("Fallo el envío del email de verificación a %s", user.email)

        return RegisterUserOutput(
            user_id=user.id, email=user.email, requires_verification=True
        )


class LoginUser:
    """Autentica un usuario. Devuelve AuthSession (normal) o LoginPending (2FA)."""

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_repo: RefreshTokenRepository,
        pending_repo: TwoFactorPendingRepository,
        *,
        password_verifier: Callable[[str, str], bool],
        token_creator: Callable[[str, str], str],
        require_verified: bool = True,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo
        self._pending_repo = pending_repo
        self._password_verifier = password_verifier
        self._token_creator = token_creator
        self._require_verified = require_verified

    def execute(self, email: str, password: str) -> LoginOutcome:
        normalized_email = email.strip().lower()
        user = self._user_repo.get_by_email(normalized_email)
        if user is None or not self._password_verifier(password, user.password_hash):
            raise InvalidCredentialsError()
        if self._require_verified and not user.email_verified:
            raise EmailNotVerifiedError(user.email)

        # 2FA: emite pending en vez de tokens
        if user.totp_enabled and user.totp_secret_encrypted is not None:
            # Limpiar pendings viejos del user (defensa)
            self._pending_repo.delete_for_user(user.id)
            return _issue_2fa_pending(user, self._pending_repo)

        return _issue_auth_session(user, self._refresh_repo, self._token_creator)


class VerifyEmail:
    """Verifica el email de un usuario via token one-shot.

    Devuelve AuthSession (normal) o LoginPending (2FA habilitado).
    """

    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: EmailVerificationTokenRepository,
        refresh_repo: RefreshTokenRepository,
        pending_repo: TwoFactorPendingRepository,
        *,
        token_creator: Callable[[str, str], str],
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._refresh_repo = refresh_repo
        self._pending_repo = pending_repo
        self._token_creator = token_creator

    def execute(self, raw_token: str) -> LoginOutcome:
        token_hash = hash_token(raw_token)
        token = self._token_repo.get_by_hash(token_hash)
        if token is None:
            raise InvalidTokenError()
        now = datetime.now(timezone.utc)
        if token.is_expired(now):
            self._token_repo.delete(token.id)
            raise TokenExpiredError()

        user = self._user_repo.get_by_id(token.user_id)
        if user is None:
            self._token_repo.delete(token.id)
            raise InvalidTokenError()

        if not user.email_verified:
            user.email_verified = True
            user.email_verified_at = now
            self._user_repo.update(user)

        self._token_repo.delete(token.id)

        # Si tiene 2FA, va al pending
        if user.totp_enabled and user.totp_secret_encrypted is not None:
            self._pending_repo.delete_for_user(user.id)
            return _issue_2fa_pending(user, self._pending_repo)

        return _issue_auth_session(user, self._refresh_repo, self._token_creator)


class RefreshSession:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_repo: RefreshTokenRepository,
        *,
        token_creator: Callable[[str, str], str],
        refresh_ttl_days: int = 30,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo
        self._token_creator = token_creator
        self._refresh_ttl_days = refresh_ttl_days

    def execute(self, raw_refresh: str) -> AuthSession:
        if not raw_refresh or not raw_refresh.strip():
            raise InvalidTokenError()
        token_hash = hash_refresh_token(raw_refresh.strip())
        token = self._refresh_repo.get_by_hash(token_hash)
        if token is None:
            raise InvalidTokenError()

        if token.is_revoked():
            self._refresh_repo.revoke_family(token.family_id)
            raise RefreshTokenReuseDetectedError()

        now = datetime.now(timezone.utc)
        if token.is_expired(now):
            raise TokenExpiredError()

        user = self._user_repo.get_by_id(token.user_id)
        if user is None:
            self._refresh_repo.mark_revoked(token.id)
            raise InvalidTokenError()

        new_raw = generate_refresh_token()
        new_token = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_refresh_token(new_raw),
            family_id=token.family_id,
            expires_at=now + timedelta(days=self._refresh_ttl_days),
            created_at=now,
        )
        self._refresh_repo.create(new_token)
        self._refresh_repo.mark_revoked(token.id, replaced_by_id=new_token.id)

        return AuthSession(
            user_id=user.id,
            email=user.email,
            access_token=self._token_creator(user.id, user.email),
            refresh_token=new_raw,
        )


class Logout:
    def __init__(self, refresh_repo: RefreshTokenRepository) -> None:
        self._refresh_repo = refresh_repo

    def execute(self, raw_refresh: str) -> None:
        if not raw_refresh or not raw_refresh.strip():
            return
        token_hash = hash_refresh_token(raw_refresh.strip())
        token = self._refresh_repo.get_by_hash(token_hash)
        if token is None or token.is_revoked():
            return
        self._refresh_repo.mark_revoked(token.id)


class ResendVerification:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: EmailVerificationTokenRepository,
        email_sender: EmailSender,
        *,
        frontend_url: str,
        token_ttl_hours: int = 24,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._email_sender = email_sender
        self._frontend_url = frontend_url.rstrip("/")
        self._token_ttl_hours = token_ttl_hours

    def execute(self, email: str) -> None:
        normalized_email = email.strip().lower()
        user = self._user_repo.get_by_email(normalized_email)
        if user is None or user.email_verified:
            return

        self._token_repo.delete_for_user(user.id)

        now = datetime.now(timezone.utc)
        raw = generate_token()
        token = EmailVerificationToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=now + timedelta(hours=self._token_ttl_hours),
            created_at=now,
        )
        self._token_repo.create(token)

        verify_url = f"{self._frontend_url}/verify-email?token={raw}"
        subject, html, text = verification_email(
            verify_url=verify_url, frontend_url=self._frontend_url
        )
        try:
            self._email_sender.send(to=user.email, subject=subject, html=html, text=text)
        except Exception:
            log.exception("Fallo el re-envío de verificación a %s", user.email)


class ForgotPassword:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: PasswordResetTokenRepository,
        refresh_repo: RefreshTokenRepository,
        email_sender: EmailSender,
        *,
        frontend_url: str,
        token_ttl_hours: int = 1,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._refresh_repo = refresh_repo
        self._email_sender = email_sender
        self._frontend_url = frontend_url.rstrip("/")
        self._token_ttl_hours = token_ttl_hours

    def execute(self, email: str) -> None:
        normalized_email = email.strip().lower()
        user = self._user_repo.get_by_email(normalized_email)
        if user is None:
            return

        self._token_repo.delete_for_user(user.id)

        now = datetime.now(timezone.utc)
        raw = generate_token()
        token = PasswordResetToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=now + timedelta(hours=self._token_ttl_hours),
            created_at=now,
        )
        self._token_repo.create(token)

        reset_url = f"{self._frontend_url}/reset-password?token={raw}"
        subject, html, text = password_reset_email(
            reset_url=reset_url, frontend_url=self._frontend_url
        )
        try:
            self._email_sender.send(to=user.email, subject=subject, html=html, text=text)
        except Exception:
            log.exception("Fallo el envío de reseteo de contraseña a %s", user.email)


class ResetPassword:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: PasswordResetTokenRepository,
        refresh_repo: RefreshTokenRepository,
        *,
        password_hasher: Callable[[str], str],
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._refresh_repo = refresh_repo
        self._password_hasher = password_hasher

    def execute(self, raw_token: str, new_password: str) -> None:
        if not new_password or len(new_password) < 6:
            raise ValidationError("new_password", "Debe tener al menos 6 caracteres")

        token_hash = hash_token(raw_token)
        token = self._token_repo.get_by_hash(token_hash)
        if token is None:
            raise InvalidTokenError()
        now = datetime.now(timezone.utc)
        if token.is_expired(now):
            self._token_repo.delete(token.id)
            raise TokenExpiredError()

        user = self._user_repo.get_by_id(token.user_id)
        if user is None:
            self._token_repo.delete(token.id)
            raise InvalidTokenError()

        user.password_hash = self._password_hasher(new_password)
        self._user_repo.update(user)

        self._token_repo.delete_for_user(user.id)
        self._refresh_repo.revoke_all_for_user(user.id)


# ── 2FA / TOTP ────────────────────────────────────────────────────────────


@dataclass
class TotpSetupStart:
    """Output de SetupTotpStart. El cliente debe mostrar QR + manual_key."""

    qr_data_url: str  # data:image/png;base64,... listo para <img>
    manual_key: str  # base32 secret, para ingreso manual
    otpauth_uri: str  # otpauth:// URI


class SetupTotpStart:
    """Genera un secret nuevo (encrypt + guarda en user, NO habilita todavía)."""

    def __init__(
        self,
        user_repo: UserRepository,
    ) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: str) -> TotpSetupStart:
        from ..infrastructure.auth.totp import (
            encrypt_secret,
            generate_totp_secret,
            provisioning_uri,
        )
        from ..infrastructure.auth.qr import make_qr_data_url

        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError()
        if user.totp_enabled:
            raise TwoFactorAlreadyEnabledError()

        plain = generate_totp_secret()
        user.totp_secret_encrypted = encrypt_secret(plain)
        # totp_enabled queda en False hasta que el user confirme con un code válido
        self._user_repo.update(user)

        uri = provisioning_uri(plain, user.email)
        return TotpSetupStart(
            qr_data_url=make_qr_data_url(uri),
            manual_key=plain,
            otpauth_uri=uri,
        )


@dataclass
class TotpSetupConfirm:
    """Output de SetupTotpConfirm. Incluye los backup codes (mostrar UNA sola vez)."""

    backup_codes: list[str]


class SetupTotpConfirm:
    """Verifica el primer code del usuario contra el secret pending y habilita 2FA."""

    def __init__(
        self,
        user_repo: UserRepository,
        backup_repo: BackupCodeRepository,
    ) -> None:
        self._user_repo = user_repo
        self._backup_repo = backup_repo

    def execute(self, user_id: str, code: str) -> TotpSetupConfirm:
        from ..infrastructure.auth.totp import (
            decrypt_secret,
            generate_backup_codes,
            verify_totp,
        )

        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError()
        if user.totp_enabled:
            raise TwoFactorAlreadyEnabledError()
        if user.totp_secret_encrypted is None:
            raise TwoFactorNotEnabledError()

        plain = decrypt_secret(user.totp_secret_encrypted)
        if not verify_totp(plain, code):
            raise InvalidTwoFactorCodeError()

        # OK — habilitar 2FA y generar backup codes
        now = datetime.now(timezone.utc)
        user.totp_enabled = True
        user.totp_enabled_at = now
        self._user_repo.update(user)

        # Generar y persistir backup codes
        pairs = generate_backup_codes(n=10)
        now = datetime.now(timezone.utc)
        entities = [
            BackupCode(
                id=str(uuid.uuid4()),
                user_id=user.id,
                code_hash=p.hash,
                created_at=now,
            )
            for p in pairs
        ]
        self._backup_repo.create_many(entities)

        return TotpSetupConfirm(backup_codes=[p.raw for p in pairs])


class VerifyTwoFactor:
    """Canjea un pending_token + code (TOTP o backup) por AuthSession."""

    def __init__(
        self,
        user_repo: UserRepository,
        pending_repo: TwoFactorPendingRepository,
        backup_repo: BackupCodeRepository,
        refresh_repo: RefreshTokenRepository,
        *,
        token_creator: Callable[[str, str], str],
    ) -> None:
        self._user_repo = user_repo
        self._pending_repo = pending_repo
        self._backup_repo = backup_repo
        self._refresh_repo = refresh_repo
        self._token_creator = token_creator

    def execute(self, raw_pending: str, code: str) -> AuthSession:
        from ..infrastructure.auth.totp import (
            decrypt_secret,
            hash_backup_code,
            looks_like_backup_code,
            verify_totp,
        )

        if not raw_pending or not raw_pending.strip() or not code or not code.strip():
            raise InvalidTwoFactorCodeError()

        token_hash = hash_token(raw_pending.strip())
        pending = self._pending_repo.get_by_hash(token_hash)
        if pending is None:
            raise InvalidTwoFactorCodeError()
        now = datetime.now(timezone.utc)
        if pending.is_expired(now):
            self._pending_repo.delete(pending.id)
            raise InvalidTwoFactorCodeError()

        user = self._user_repo.get_by_id(pending.user_id)
        if user is None or not user.totp_enabled or user.totp_secret_encrypted is None:
            self._pending_repo.delete(pending.id)
            raise InvalidTwoFactorCodeError()

        code_ok = False

        # Heurística: si parece backup code, intentar primero por backup
        if looks_like_backup_code(code):
            backup = self._backup_repo.get_by_hash(
                user.id, hash_backup_code(code)
            )
            if backup is not None and not backup.is_used():
                self._backup_repo.mark_used(backup.id)
                code_ok = True

        # Si no fue backup, intentar TOTP
        if not code_ok:
            plain = decrypt_secret(user.totp_secret_encrypted)
            if verify_totp(plain, code):
                code_ok = True

        if not code_ok:
            raise InvalidTwoFactorCodeError()

        # OK — emitir sesión y limpiar pending
        self._pending_repo.delete(pending.id)
        return _issue_auth_session(user, self._refresh_repo, self._token_creator)


class DisableTotp:
    """Deshabilita 2FA. Requiere password + (TOTP code O backup code)."""

    def __init__(
        self,
        user_repo: UserRepository,
        backup_repo: BackupCodeRepository,
        *,
        password_verifier: Callable[[str, str], bool],
    ) -> None:
        self._user_repo = user_repo
        self._backup_repo = backup_repo
        self._password_verifier = password_verifier

    def execute(self, user_id: str, password: str, code: str) -> None:
        from ..infrastructure.auth.totp import (
            decrypt_secret,
            hash_backup_code,
            looks_like_backup_code,
            verify_totp,
        )

        if not password or not code:
            raise InvalidCredentialsError()

        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError()
        if not user.totp_enabled or user.totp_secret_encrypted is None:
            raise TwoFactorNotEnabledError()
        if not self._password_verifier(password, user.password_hash):
            raise InvalidCredentialsError()

        # Verificar code (TOTP o backup)
        code_ok = False
        if looks_like_backup_code(code):
            backup = self._backup_repo.get_by_hash(
                user.id, hash_backup_code(code)
            )
            if backup is not None and not backup.is_used():
                self._backup_repo.mark_used(backup.id)
                code_ok = True
        if not code_ok:
            plain = decrypt_secret(user.totp_secret_encrypted)
            if verify_totp(plain, code):
                code_ok = True
        if not code_ok:
            raise InvalidTwoFactorCodeError()

        # OK — deshabilitar
        user.totp_enabled = False
        user.totp_secret_encrypted = None
        user.totp_enabled_at = None
        self._user_repo.update(user)
        self._backup_repo.delete_all_for_user(user.id)


class RegenerateBackupCodes:
    """Regenera los backup codes. Requiere password (anti-abuso)."""

    def __init__(
        self,
        user_repo: UserRepository,
        backup_repo: BackupCodeRepository,
        *,
        password_verifier: Callable[[str, str], bool],
    ) -> None:
        self._user_repo = user_repo
        self._backup_repo = backup_repo
        self._password_verifier = password_verifier

    def execute(self, user_id: str, password: str) -> list[str]:
        from ..infrastructure.auth.totp import generate_backup_codes

        if not password:
            raise InvalidCredentialsError()

        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError()
        if not self._password_verifier(password, user.password_hash):
            raise InvalidCredentialsError()
        if not user.totp_enabled:
            raise TwoFactorNotEnabledError()

        # Borrar viejos y generar nuevos
        self._backup_repo.delete_all_for_user(user.id)
        pairs = generate_backup_codes(n=10)
        now = datetime.now(timezone.utc)
        entities = [
            BackupCode(
                id=str(uuid.uuid4()),
                user_id=user.id,
                code_hash=p.hash,
                created_at=now,
            )
            for p in pairs
        ]
        self._backup_repo.create_many(entities)
        return [p.raw for p in pairs]
