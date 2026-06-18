from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from ...domain.exceptions import UnauthorizedError

JWT_SECRET_KEY_ENV = "JWT_SECRET_KEY"


def _get_secret() -> str:
    key = os.environ.get(JWT_SECRET_KEY_ENV) or current_app.config.get(
        "SECRET_KEY"
    ) or os.environ.get("SECRET_KEY", "")
    if not key:
        raise RuntimeError(
            "Falta JWT_SECRET_KEY o SECRET_KEY en el entorno. "
            "Configurala antes de iniciar."
        )
    return key


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def verify_token(bearer_token: str) -> str:
    """Devuelve el user_id o lanza UnauthorizedError."""
    if not bearer_token or not bearer_token.strip():
        raise UnauthorizedError("Falta el token de autenticación")
    token = bearer_token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token expirado")
    except jwt.PyJWTError as e:
        raise UnauthorizedError(f"Token inválido: {e}")


def decode_token(bearer_token: str) -> dict:
    """Devuelve el payload completo del token."""
    token = bearer_token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    try:
        return jwt.decode(token, _get_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise UnauthorizedError(f"Token inválido: {e}")
