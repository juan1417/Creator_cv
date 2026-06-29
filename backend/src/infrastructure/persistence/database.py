"""Inicialización del engine de base de datos.

Soporta dos backends:
- **SQLite** (dev/tests, default si no hay `DATABASE_URL`).
- **PostgreSQL** (Neon en producción), vía driver `psycopg` v3.

Lee `DATABASE_URL` del entorno. Si es Postgres y no especifica driver ni
`sslmode`, los agrega automáticamente. Activa `pool_pre_ping` para tolerar
que Neon escale a cero y cierre conexiones dormidas.
"""
from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None

# URL por defecto (SQLite local, solo si no se setea DATABASE_URL).
_DEFAULT_SQLITE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data"
)
_DEFAULT_SQLITE_PATH = os.path.join(_DEFAULT_SQLITE_DIR, "creator_cv.sqlite3")


def _normalize_driver(url: str) -> str:
    """Convierte ``postgres://`` o ``postgresql://`` a ``postgresql+psycopg://``.

    Si la URL ya trae un driver explícito (``postgresql+psycopg2://`` etc.) no
    se toca.
    """
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def is_postgres(url: str) -> bool:
    """True si la URL apunta a Postgres (Neon u otro).

    Acepta tanto la forma ``postgres://`` / ``postgresql://`` como la
    normalizada con driver explícito ``postgresql+psycopg://``.
    """
    return url.startswith(("postgres://", "postgresql://", "postgresql+"))


def get_db_url() -> str:
    """Devuelve la URL lista para ``create_engine``.

    Prioridad: ``DATABASE_URL`` del entorno > SQLite local por defecto.
    """
    raw = os.environ.get("DATABASE_URL", "").strip()
    if raw:
        return _normalize_driver(raw)
    os.makedirs(_DEFAULT_SQLITE_DIR, exist_ok=True)
    return f"sqlite:///{_DEFAULT_SQLITE_PATH}"


def init_db(echo: bool = False) -> Engine:
    """Inicializa el engine global. Idempotente."""
    global _engine, _SessionLocal
    url = get_db_url()

    engine_kwargs: dict = {"echo": echo, "future": True}

    if is_postgres(url):
        # Neon escala a cero: pool_pre_ping evita "SSL connection has been closed".
        # pool_recycle bajo porque Neon cierra conexiones idle agresivamente.
        connect_args: dict = {}
        if "sslmode=" not in url:
            connect_args["sslmode"] = "require"
        engine_kwargs.update(
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
        )
    else:
        # SQLite: necesario para uso con Flask en threads.
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    _engine = create_engine(url, **engine_kwargs)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)

    # Registrar listeners en la INSTANCIA del engine (no en la clase Engine).
    # Antes se hacía con @event.listens_for(Engine, "connect") lo cual filtraba
    # el PRAGMA de SQLite a conexiones de cualquier engine creado en el proceso.
    if is_postgres(url):

        @event.listens_for(_engine, "connect")
        def _set_pg_session(dbapi_connection, connection_record):  # noqa: ARG001
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET TIME ZONE 'UTC'")
                cursor.execute("SET statement_timeout = '30s'")

    else:

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Asegurar que los modelos quedan registrados antes de cualquier uso.
    import src.infrastructure.persistence.models  # noqa: F401

    return _engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        init_db()
    return _engine


def create_all() -> None:
    """Crea todas las tablas declaradas en ``Base.metadata``.

    Solo usar para SQLite (dev/tests). Para Postgres las maneja Alembic
    (``alembic upgrade head``) — no se llama automáticamente.
    """
    from sqlalchemy.orm import configure_mappers

    from .models import Base

    configure_mappers()
    Base.metadata.create_all(bind=get_engine())


@contextmanager
def get_session() -> Generator[Session, None, None]:
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    if _SessionLocal is None:
        raise RuntimeError("Database not initialised")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
