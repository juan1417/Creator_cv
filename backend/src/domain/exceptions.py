"""Excepciones del dominio.

Las capas superiores (application, infrastructure) las capturan
y traducen a errores HTTP o rethrow.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base para todos los errores de dominio."""


class CVNotFoundError(DomainError):
    """El CV no existe o el usuario no tiene acceso."""

    def __init__(self, cv_id: str) -> None:
        super().__init__(f"CV {cv_id!r} no encontrado")
        self.cv_id = cv_id


class ChatNotFoundError(DomainError):
    """El chat no existe (no se inicializó aún)."""

    def __init__(self, cv_id: str) -> None:
        super().__init__(f"Chat del CV {cv_id!r} no encontrado")
        self.cv_id = cv_id


class UnauthorizedError(DomainError):
    """El usuario no tiene permiso para esta operación."""

    def __init__(self, message: str = "No autorizado") -> None:
        super().__init__(message)


class ValidationError(DomainError):
    """Los datos de entrada no pasan la validación."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
