"""Generación y verificación de tokens opacos (verificación email, reset password).

A diferencia de los JWTs (que son firmados y decodificables), estos tokens son
strings aleatorios que la DB solo conoce por su hash SHA-256. Si la DB se
filtra, los atacantes no pueden usar los tokens porque solo tienen el hash.

Flujo:
1. Server genera token crudo: ``secrets.token_urlsafe(32)``
2. Server calcula hash:      ``hashlib.sha256(token).hexdigest()``
3. Server guarda el hash en la DB
4. Server envía el token crudo al usuario por email
5. Usuario hace click en el link (con token crudo)
6. Server hashea el token recibido y lo busca por hash en la DB
"""
from __future__ import annotations

import hashlib
import secrets


def generate_token() -> str:
    """Genera un token URL-safe aleatorio (43 chars, 32 bytes de entropía)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Devuelve el SHA-256 hex del token. Es lo que se guarda en la DB."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
