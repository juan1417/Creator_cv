"""Flask-Limiter setup para rate limiting en endpoints sensibles.

Rate limits aplicados (decoradores en ``routes.py``):
- ``/auth/register``             → 5/hour por IP
- ``/auth/login``                → 10/15min por IP+email (anti credential stuffing)
- ``/auth/forgot-password``      → 3/hour por IP
- ``/auth/resend-verification``  → 3/hour por IP+email

Storage: Postgres (compartido con la app principal). ``limits`` v5.x no
incluye backend Postgres nativo, así que enchufamos un
``PostgresRateLimitStorage`` custom (``postgres_limiter_storage.py``).
"""
from __future__ import annotations

from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from limits.storage.memory import MemoryStorage

from ..persistence.database import get_db_url, is_postgres
from .postgres_limiter_storage import PostgresRateLimitStorage


def get_login_key() -> str:
    """Combina IP + email normalizado para defender contra credential stuffing.

    Si no se puede leer el email del body (request mal formado), cae a IP sola.
    """
    ip = get_remote_address()
    try:
        body = request.get_json(silent=True) or {}
        email = (body.get("email") or "").strip().lower()
    except Exception:
        email = ""
    return f"{ip}:{email}" if email else ip


def get_email_key() -> str:
    """IP + email, usado por resend-verification."""
    ip = get_remote_address()
    try:
        body = request.get_json(silent=True) or {}
        email = (body.get("email") or "").strip().lower()
    except Exception:
        email = ""
    return f"{ip}:{email}" if email else ip


# Instancia global del limiter — los decorators en routes.py la usan directamente.
# Storage se asigna en ``register_limiter()`` (necesita app ya creada).
limiter = Limiter(
    key_func=get_remote_address,
    headers_enabled=True,
    default_limits=[],  # sin default global, solo específicos por endpoint
    in_memory_fallback_enabled=True,  # si Postgres cae, cae a memory (no rompe auth)
)


def register_limiter(app: Flask) -> None:
    """Vincula el limiter a la app Flask con el storage apropiado.

    Para Postgres: usa ``PostgresRateLimitStorage`` (custom).
    Para otros: ``MemoryStorage`` (útil en tests; los límites no persisten).
    """
    if is_postgres(get_db_url()):
        storage = PostgresRateLimitStorage(uri=get_db_url())
    else:
        storage = MemoryStorage()

    # Init app con un placeholder URI; luego sobreescribimos el storage.
    # (Flask-Limiter no acepta ``storage=`` por constructor en esta versión.)
    app.config["RATELIMIT_STORAGE_URI"] = "memory://"
    limiter.init_app(app)

    # Override: enchufamos el storage real (Postgres o memory) y reconstruimos
    # el strategy wrapper para que use la instancia nueva.
    limiter._storage = storage
    from limits import strategies

    limiter._limiter = strategies.STRATEGIES[limiter._strategy](storage)
