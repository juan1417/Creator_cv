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


# ── Auth ─────────────────────────────────────────────────────────────────


class UserAlreadyExistsError(DomainError):
    """Se intenta registrar un email que ya existe."""

    def __init__(self, email: str) -> None:
        super().__init__(f"El email {email!r} ya está registrado")
        self.email = email


class InvalidCredentialsError(DomainError):
    """Email o contraseña incorrectos."""

    def __init__(self) -> None:
        super().__init__("Email o contraseña incorrectos")


class EmailNotVerifiedError(DomainError):
    """El usuario existe pero todavía no verificó su email."""

    def __init__(self, email: str) -> None:
        super().__init__(
            f"Debes verificar tu email antes de iniciar sesión. "
            f"Revisá tu casilla en {email!r}."
        )
        self.email = email


class InvalidTokenError(DomainError):
    """El token (verificación o reset) no existe o ya fue usado."""

    def __init__(self) -> None:
        super().__init__("El enlace no es válido o ya fue utilizado")


class TokenExpiredError(DomainError):
    """El token existía pero pasó su fecha de expiración."""

    def __init__(self) -> None:
        super().__init__("El enlace expiró. Solicitá uno nuevo.")


class RefreshTokenReuseDetectedError(DomainError):
    """Se intentó usar un refresh token ya revocado.

    Esto es señal de robo: el refresh original fue usado legítimamente (rotó),
    y alguien está intentando reusar el viejo. Invalidamos TODA la family
    para forzar re-login en todos los devices.
    """

    def __init__(self) -> None:
        super().__init__(
            "Sesión inválida. Por seguridad volvé a iniciar sesión."
        )


# ── 2FA ──────────────────────────────────────────────────────────────────


class TwoFactorRequiredError(DomainError):
    """Login requiere un segundo paso (TOTP o backup code)."""

    def __init__(self, pending_token: str) -> None:
        super().__init__("Verificación en dos pasos requerida")
        self.pending_token = pending_token


class InvalidTwoFactorCodeError(DomainError):
    """El código TOTP o backup code es inválido / expirado."""

    def __init__(self) -> None:
        super().__init__("Código inválido")


class TwoFactorNotEnabledError(DomainError):
    """Se intentó una operación 2FA con un user que no lo tiene habilitado."""

    def __init__(self) -> None:
        super().__init__("La verificación en dos pasos no está habilitada")


class TwoFactorAlreadyEnabledError(DomainError):
    """Se intentó habilitar 2FA cuando ya está habilitado."""

    def __init__(self) -> None:
        super().__init__("La verificación en dos pasos ya está habilitada")
