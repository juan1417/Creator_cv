"""Traduce excepciones del dominio a respuestas HTTP.

El dominio lanza DomainError (o subclases). La capa web los traduce a
códigos HTTP correctos, sin que el dominio sepa de HTTP.
"""
from __future__ import annotations

from flask import Flask, jsonify
from flask_limiter.errors import RateLimitExceeded

from ...domain.exceptions import (
    CVNotFoundError,
    ChatNotFoundError,
    DomainError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    UnauthorizedError,
    UserAlreadyExistsError,
    ValidationError,
)


def _err(message: str, code: int):
    return jsonify({"ok": False, "error": message}), code


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def _on_validation(e: ValidationError):
        return _err(str(e), 400)

    @app.errorhandler(InvalidCredentialsError)
    def _on_invalid_creds(_e: InvalidCredentialsError):
        return _err("Email o contraseña incorrectos", 401)

    @app.errorhandler(EmailNotVerifiedError)
    def _on_email_not_verified(_e: EmailNotVerifiedError):
        return _err(str(_e), 403)

    @app.errorhandler(InvalidTokenError)
    def _on_invalid_token(_e: InvalidTokenError):
        return _err(str(_e), 400)

    @app.errorhandler(TokenExpiredError)
    def _on_token_expired(_e: TokenExpiredError):
        return _err(str(_e), 400)

    @app.errorhandler(UserAlreadyExistsError)
    def _on_user_exists(_e: UserAlreadyExistsError):
        return _err("El email ya está registrado", 409)

    @app.errorhandler(UnauthorizedError)
    def _on_unauth(e: UnauthorizedError):
        return _err(str(e), 401)

    @app.errorhandler(CVNotFoundError)
    def _on_not_found(e: CVNotFoundError):
        return _err(str(e), 404)

    @app.errorhandler(ChatNotFoundError)
    def _on_chat_not_found(e: ChatNotFoundError):
        return _err(str(e), 404)

    @app.errorhandler(RateLimitExceeded)
    def _on_rate_limit(e: RateLimitExceeded):
        return _err("Demasiados intentos. Probá más tarde.", 429)

    @app.errorhandler(DomainError)
    def _on_domain(e: DomainError):
        return _err(str(e), 400)

    @app.errorhandler(404)
    def _on_404(_e):
        return _err("Recurso no encontrado", 404)

    @app.errorhandler(405)
    def _on_405(_e):
        return _err("Método no permitido", 405)

    @app.errorhandler(500)
    def _on_500(e):
        app.logger.exception("Error interno del servidor")
        return _err("Error interno del servidor", 500)
