"""Repository interfaces: contratos que la infrastructure debe implementar.

El dominio define QUÉ se puede hacer con los datos, no CÓMO.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence

from .entities import (
    CV,
    ChatMessage,
    BackupCode,
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    TwoFactorPending,
    User,
)


class UserRepository(ABC):
    """Contrato para persistir usuarios."""

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        """Devuelve el user por id, o None si no existe."""

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Devuelve el user por email (normalizado a lowercase), o None."""

    @abstractmethod
    def create(self, user: User) -> User:
        """Crea un nuevo user. Lanza UserAlreadyExistsError si el email ya existe."""

    @abstractmethod
    def update(self, user: User) -> User:
        """Actualiza un user existente. Lanza UserAlreadyExistsError si el email cambió y choca."""


class CVRepository(ABC):
    """Contrato para persistir CVs. El user_id es el dueño."""

    @abstractmethod
    def create(self, cv: CV) -> CV:
        """Crea un CV y lo persiste. Devuelve el CV con su id."""
        ...

    @abstractmethod
    def get(self, cv_id: str, user_id: str) -> CV:
        """Obtiene un CV por id. Lanza CVNotFoundError si no existe
        o no pertenece al usuario."""
        ...

    @abstractmethod
    def list_for_user(self, user_id: str) -> Sequence[CV]:
        """Lista todos los CVs de un usuario, ordenados por updated_at desc."""
        ...

    @abstractmethod
    def update(self, cv: CV) -> CV:
        """Actualiza un CV existente. Asume que ya fue validado por el caller."""
        ...

    @abstractmethod
    def delete(self, cv_id: str, user_id: str) -> None:
        """Elimina un CV. Lanza CVNotFoundError si no existe o no pertenece al user."""
        ...


class ChatRepository(ABC):
    """Contrato para persistir el historial de chat de un CV."""

    @abstractmethod
    def get_messages(self, cv_id: str, user_id: str) -> list[ChatMessage]:
        """Devuelve los mensajes del chat. Lista vacía si no hay."""
        ...

    @abstractmethod
    def append(self, cv_id: str, user_id: str, message: ChatMessage) -> None:
        """Agrega un mensaje al final del chat."""
        ...

    @abstractmethod
    def clear(self, cv_id: str, user_id: str) -> None:
        """Limpia todo el historial del chat."""
        ...


class EmailVerificationTokenRepository(ABC):
    """Contrato para tokens de verificación de email (one-shot, expiran)."""

    @abstractmethod
    def create(self, token: EmailVerificationToken) -> EmailVerificationToken:
        """Persiste un nuevo token."""

    @abstractmethod
    def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        """Busca por el hash del token crudo (nunca se guarda el crudo)."""

    @abstractmethod
    def delete(self, token_id: str) -> None:
        """Elimina un token (usado o expirado)."""

    @abstractmethod
    def delete_for_user(self, user_id: str) -> int:
        """Elimina todos los tokens pendientes de un user. Devuelve la cantidad borrada."""


class PasswordResetTokenRepository(ABC):
    """Contrato para tokens de reseteo de contraseña (one-shot, expiran)."""

    @abstractmethod
    def create(self, token: PasswordResetToken) -> PasswordResetToken:
        """Persiste un nuevo token."""

    @abstractmethod
    def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        """Busca por el hash del token crudo."""

    @abstractmethod
    def delete(self, token_id: str) -> None:
        """Elimina un token (usado o expirado)."""

    @abstractmethod
    def delete_for_user(self, user_id: str) -> int:
        """Elimina todos los tokens pendientes de un user."""


class RefreshTokenRepository(ABC):
    """Contrato para refresh tokens (rotación + family invalidation)."""

    @abstractmethod
    def create(self, token: RefreshToken) -> RefreshToken:
        """Persiste un nuevo refresh token."""

    @abstractmethod
    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Busca por hash. NO chequea revoked — el caller decide qué hacer."""

    @abstractmethod
    def mark_revoked(self, token_id: str, replaced_by_id: str | None = None) -> None:
        """Marca un refresh como revocado (rotación o logout)."""

    @abstractmethod
    def revoke_family(self, family_id: str) -> int:
        """Revoca TODOS los tokens de una family. Usado en detección de robo.
        Devuelve la cantidad revocada."""

    @abstractmethod
    def revoke_all_for_user(self, user_id: str) -> int:
        """Revoca todos los refresh tokens de un user (e.g. tras reset password).
        Devuelve la cantidad revocada."""


class BackupCodeRepository(ABC):
    """Contrato para códigos de respaldo 2FA (one-time, hasheados)."""

    @abstractmethod
    def create_many(self, codes: list[BackupCode]) -> list[BackupCode]:
        """Persiste varios códigos de una vez."""

    @abstractmethod
    def list_for_user(self, user_id: str) -> list[BackupCode]:
        """Lista TODOS los códigos del user (incluyendo usados)."""

    @abstractmethod
    def get_by_hash(self, user_id: str, code_hash: str) -> BackupCode | None:
        """Busca un código específico del user por hash."""

    @abstractmethod
    def mark_used(self, code_id: str) -> None:
        """Marca un código como usado."""

    @abstractmethod
    def delete_all_for_user(self, user_id: str) -> int:
        """Borra todos los códigos del user. Usado al regenerar o deshabilitar 2FA."""


class TwoFactorPendingRepository(ABC):
    """Contrato para tokens cortos del segundo paso del login (5 min)."""

    @abstractmethod
    def create(self, pending: TwoFactorPending) -> TwoFactorPending:
        """Persiste un nuevo pending."""

    @abstractmethod
    def get_by_hash(self, token_hash: str) -> TwoFactorPending | None:
        """Busca por hash."""

    @abstractmethod
    def delete(self, pending_id: str) -> None:
        """Borra un pending (usado o expirado)."""

    @abstractmethod
    def delete_for_user(self, user_id: str) -> int:
        """Borra todos los pendings del user."""

