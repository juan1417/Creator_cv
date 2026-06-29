"""Storage backend de Flask-Limiter contra Postgres.

``limits`` v5.x no incluye un backend nativo para Postgres (los extras
``[postgresql]`` no existen en esta versión; sólo hay memory/redis/memcached/
mongodb). Para mantener Flask-Limiter como librería (decoradores declarativos,
``X-RateLimit-*`` headers, ``Retry-After``) sin agregar Redis, implementamos
un ``Storage`` mínimo que persiste los counters en la misma DB Postgres que
usa el resto del backend.

Estrategia: ``fixed-window`` (default de Flask-Limiter). Sólo necesitamos
implementar ``incr`` / ``get`` / ``check`` / ``clear`` / ``reset``.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from limits.storage.base import Storage
from sqlalchemy import text


class PostgresRateLimitStorage(Storage):
    """Backend Postgres para Flask-Limiter / limits.

    Tabla propia ``rate_limit_counters`` (NO la maneja Alembic — la crea este
    storage en su primera conexión). Una fila por ``(key)`` con ``count`` y
    ``expires_at``. Al hacer ``incr(key, expiry)``:

    - Si la fila no existe → la crea con count=1, expires_at=now+expiry.
    - Si existe y NO expiró → count += 1, expires_at se mantiene.
    - Si existe y SÍ expiró → reset: count=1, expires_at=now+expiry.

    Devuelve siempre el nuevo ``count``, que es lo que Flask-Limiter espera
    para decidir si la request excede el límite.
    """

    # Flask-Limiter usa este atributo cuando parsea URIs. Como pasamos la
    # instancia directamente, no se usa, pero tiene que existir.
    STORAGE_SCHEME = "postgresql+psycopg"
    DEPENDENCIES = []  # psycopg ya está en pyproject

    def __init__(self, uri: str | None = None, **options) -> None:
        super().__init__(uri, **options)
        # Reutilizamos el engine global de la app (ya configurado con pool,
        # ssl, etc.). NO creamos un engine propio.
        from src.infrastructure.persistence.database import get_engine

        self._engine = get_engine()
        self._table_ready = False

    def _ensure_table(self) -> None:
        """Crea la tabla si no existe. Se llama lazy desde cada operación."""
        if self._table_ready:
            return
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS rate_limit_counters (
                        key TEXT PRIMARY KEY,
                        count INTEGER NOT NULL DEFAULT 0,
                        expires_at TIMESTAMPTZ
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_rate_limit_counters_expires "
                    "ON rate_limit_counters(expires_at)"
                )
            )
        self._table_ready = True

    def incr(self, key: str, expiry: float, amount: int = 1) -> int:
        """Incrementa el counter. Si expiró, lo resetea."""
        self._ensure_table()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=expiry)
        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    INSERT INTO rate_limit_counters (key, count, expires_at)
                    VALUES (:key, :amount, :expires_at)
                    ON CONFLICT (key) DO UPDATE SET
                        count = CASE
                            WHEN rate_limit_counters.expires_at < :now
                                THEN :amount
                            ELSE rate_limit_counters.count + :amount
                        END,
                        expires_at = CASE
                            WHEN rate_limit_counters.expires_at < :now
                                THEN :expires_at
                            ELSE rate_limit_counters.expires_at
                        END
                    RETURNING count
                    """
                ),
                {"key": key, "amount": amount, "expires_at": expires_at, "now": now},
            ).first()
            return int(row[0]) if row else 0

    def get(self, key: str) -> int:
        self._ensure_table()
        now = datetime.now(timezone.utc)
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT count FROM rate_limit_counters "
                    "WHERE key = :key AND expires_at >= :now"
                ),
                {"key": key, "now": now},
            ).first()
            return int(row[0]) if row else 0

    def clear(self, key: str) -> None:
        self._ensure_table()
        with self._engine.begin() as conn:
            conn.execute(
                text("DELETE FROM rate_limit_counters WHERE key = :key"),
                {"key": key},
            )

    def reset(self) -> None:
        self._ensure_table()
        with self._engine.begin() as conn:
            conn.execute(text("DELETE FROM rate_limit_counters"))

    def check(self) -> bool:
        """Health check: ¿podemos hablar con la DB?"""
        try:
            self._ensure_table()
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    # El default de Flask-Limiter es fixed-window — no necesitamos sliding window.
    # Si en el futuro alguien quiere moving-window, agregar
    # ``get_sliding_window`` y ``acquire_sliding_window_entry``.

    def get_expiry(self, key: str) -> int:
        """Devuelve el unix timestamp en que expira la key, o ``0`` si no existe."""
        self._ensure_table()
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT extract(epoch from expires_at)::bigint FROM rate_limit_counters WHERE key = :key"),
                {"key": key},
            ).first()
            return int(row[0]) if row else 0

    @property
    def base_exceptions(self) -> tuple[type[BaseException], ...]:
        """Excepciones que el storage puede lanzar — Flask-Limiter las usa para
        distinguir errores de storage de errores de aplicación."""
        from sqlalchemy.exc import SQLAlchemyError

        return (SQLAlchemyError,)
