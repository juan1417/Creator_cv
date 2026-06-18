from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'creator_cv.sqlite3')}",
    )


def init_db(echo: bool = False) -> Engine:
    global _engine, _SessionLocal
    url = get_db_url()
    _engine = create_engine(url, echo=echo)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)

    import src.infrastructure.persistence.models as _  # noqa: F401

    from sqlalchemy import event

    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        if "sqlite" in url:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    _models = _  # ensure models are imported before create_all
    from sqlalchemy.orm import configure_mappers

    configure_mappers()
    _engine.connect()
    return _engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = init_db()
    return _engine


def create_all() -> None:
    from sqlalchemy.orm import configure_mappers

    configure_mappers()
    from .models import Base

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
