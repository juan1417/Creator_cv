"""Entidades del dominio: objetos con identidad propia.

Una entidad se identifica por su ID (no por sus atributos).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class User:
    """Usuario del sistema. El email es único (lower-case normalizado)."""

    id: str
    email: str
    password_hash: str
    email_verified: bool
    email_verified_at: datetime | None
    created_at: datetime
    # 2FA — Phase 3
    totp_enabled: bool = False
    totp_secret_encrypted: bytes | None = None  # Fernet(plain secret) — bytes
    totp_enabled_at: datetime | None = None


@dataclass
class CV:
    """Un CV pertenece a un usuario y tiene un contexto JSON (estructura libre)."""

    id: str
    user_id: str
    title: str
    context_json: str  # JSON serializado del contexto completo
    created_at: datetime
    updated_at: datetime

    def update_title(self, new_title: str) -> None:
        if not new_title or not new_title.strip():
            raise ValueError("El título no puede estar vacío")
        self.title = new_title.strip()
        self.updated_at = datetime.utcnow()

    def update_context(self, new_context_json: str) -> None:
        if not new_context_json or not new_context_json.strip():
            raise ValueError("El contexto no puede estar vacío")
        self.context_json = new_context_json
        self.updated_at = datetime.utcnow()


@dataclass
class ChatMessage:
    """Un mensaje de chat (user o assistant) con contenido y opcional patch JSON."""

    role: str  # "user" | "assistant"
    content: str
    patch: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.role not in ("user", "assistant"):
            raise ValueError(f"role debe ser 'user' o 'assistant', recibí {self.role!r}")
        if not self.content or not self.content.strip():
            raise ValueError("content no puede estar vacío")


@dataclass
class EmailVerificationToken:
    """Token de verificación de email (one-shot, expira)."""

    id: str
    user_id: str
    token_hash: str  # SHA-256 hex del token crudo (nunca se guarda el crudo)
    expires_at: datetime
    created_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at


@dataclass
class PasswordResetToken:
    """Token de reseteo de contraseña (one-shot, expira)."""

    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    created_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at


@dataclass
class RefreshToken:
    """Token opaco de larga duración (sesión). Se rota en cada refresh.

    ``family_id`` agrupa todos los refresh tokens de una misma cadena de
    rotación. Si alguno se reusa después de revocado, invalidamos toda la
    family (detección de robo).
    """

    id: str
    user_id: str
    token_hash: str  # SHA-256(raw)
    family_id: str
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None
    replaced_by_id: str | None = None

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at


@dataclass
class BackupCode:
    """Código de respaldo one-time para 2FA. Se muestra al usuario UNA sola vez.

    El código crudo tiene formato ``XXXX-XXXX`` (mayúsculas + dígitos). En DB
    guardamos el SHA-256 del código normalizado (sin guiones, uppercase).
    """

    id: str
    user_id: str
    code_hash: str
    used_at: datetime | None = None
    created_at: datetime | None = None

    def is_used(self) -> bool:
        return self.used_at is not None


@dataclass
class TwoFactorPending:
    """Token corto (5 min) que se emite cuando el primer paso del login (password)
    pasa pero el user tiene 2FA habilitado. Se canjea en /api/auth/2fa/verify por
    los tokens de sesión."""

    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    created_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at
