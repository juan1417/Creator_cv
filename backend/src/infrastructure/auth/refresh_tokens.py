"""Generación y hashing de refresh tokens opacos.

A diferencia de los access tokens (JWT firmado), los refresh tokens son
strings aleatorios opacos. La DB solo conoce su hash SHA-256. Esto permite
revocación real (logout, password reset, robo detectado).
"""
from __future__ import annotations

import hashlib
import secrets


def generate_refresh_token() -> str:
    """Genera un refresh token URL-safe aleatorio (43 chars, 32 bytes)."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hex del token. Es lo único que se guarda en la DB."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
