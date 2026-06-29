"""JWT y password hashing.

JWT claims (Phase 1 hardening):
- ``iss`` (issuer) — ``creator-cv-backend``
- ``aud`` (audience) — ``creator-cv``
- ``sub`` (subject) — user_id
- ``email`` — denormalizado para evitar query extra en cada request
- ``iat`` (issued at) — timestamp UTC
- ``exp`` (expiration) — configurable (default 15 min)
- ``jti`` (JWT ID) — uuid4 hex, único por token

Decode con ``leeway=30`` para tolerar clock skew entre server y cliente.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from ...domain.exceptions import UnauthorizedError

JWT_SECRET_KEY_ENV = "JWT_SECRET_KEY"
JWT_ISSUER = "creator-cv-backend"
JWT_AUDIENCE = "creator-cv"
JWT_LEEWAY_SECONDS = 30


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


def _get_access_ttl_minutes() -> int:
    """TTL del access token en minutos. Default 15. Configurable vía env."""
    raw = os.environ.get("ACCESS_TOKEN_TTL_MINUTES", "15").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 15


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def create_access_token(user_id: str, email: str) -> str:
    """Emite un access token JWT firmado.

    Usado por ``LoginUser``, ``VerifyEmail``, ``VerifyTwoFactor`` y
    ``RefreshSession`` (después de rotar el refresh).
    """
    now = datetime.now(timezone.utc)
    ttl_minutes = _get_access_ttl_minutes()
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


# Backwards-compat: rutas/routes.py siguen llamando ``create_token``.
# Alias para no romper imports existentes.
create_token = create_access_token


def _decode(token: str) -> dict:
    return jwt.decode(
        token,
        _get_secret(),
        algorithms=["HS256"],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
        leeway=JWT_LEEWAY_SECONDS,
        options={"require": ["exp", "iat", "sub", "iss", "aud", "jti"]},
    )


def verify_token(bearer_token: str) -> str:
    """Devuelve el user_id o lanza UnauthorizedError."""
    if not bearer_token or not bearer_token.strip():
        raise UnauthorizedError("Falta el token de autenticación")
    token = bearer_token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    try:
        payload = _decode(token)
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token expirado")
    except jwt.InvalidIssuerError:
        raise UnauthorizedError("Token de origen inválido")
    except jwt.InvalidAudienceError:
        raise UnauthorizedError("Token de audiencia inválida")
    except jwt.MissingRequiredClaimError as e:
        raise UnauthorizedError(f"Token mal formado: falta claim {e.claim!r}")
    except jwt.PyJWTError as e:
        raise UnauthorizedError(f"Token inválido: {e}")


def decode_token(bearer_token: str) -> dict:
    """Devuelve el payload completo del token."""
    token = bearer_token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    try:
        return _decode(token)
    except jwt.PyJWTError as e:
        raise UnauthorizedError(f"Token inválido: {e}")
