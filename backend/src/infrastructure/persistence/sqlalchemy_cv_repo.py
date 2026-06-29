from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select

from ...domain.entities import CV
from ...domain.exceptions import CVNotFoundError
from ...domain.repositories import CVRepository
from .database import get_session
from .models import CVModel


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    """Acepta string o UUID y devuelve ``uuid.UUID``."""
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _row_to_cv(row: CVModel) -> CV:
    """Convierte una fila ORM a entidad de dominio (IDs como ``str``,
    ``context_json`` como string JSON serializado)."""
    return CV(
        id=str(row.id),
        user_id=str(row.user_id),
        title=row.title,
        context_json=json.dumps(row.context_json, ensure_ascii=False, indent=2),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyCVRepository(CVRepository):
    def create(self, cv: CV) -> CV:
        with get_session() as session:
            kwargs: dict = dict(
                user_id=_to_uuid(cv.user_id),
                title=cv.title,
                context_json=json.loads(cv.context_json),
            )
            # Si la entidad ya trae id (ej. seed), respetarlo; si no, default del modelo.
            if cv.id:
                kwargs["id"] = _to_uuid(cv.id)
            model = CVModel(**kwargs)
            session.add(model)
            session.flush()
            return _row_to_cv(model)

    def get(self, cv_id: str, user_id: str) -> CV:
        with get_session() as session:
            row = session.scalar(
                select(CVModel).where(
                    CVModel.id == _to_uuid(cv_id),
                    CVModel.user_id == _to_uuid(user_id),
                )
            )
            if not row:
                raise CVNotFoundError(cv_id)
            return _row_to_cv(row)

    def list_for_user(self, user_id: str) -> Sequence[CV]:
        with get_session() as session:
            rows = session.scalars(
                select(CVModel)
                .where(CVModel.user_id == _to_uuid(user_id))
                .order_by(CVModel.updated_at.desc())
            ).all()
            return [_row_to_cv(r) for r in rows]

    def update(self, cv: CV) -> CV:
        with get_session() as session:
            row = session.scalar(
                select(CVModel).where(
                    CVModel.id == _to_uuid(cv.id),
                    CVModel.user_id == _to_uuid(cv.user_id),
                )
            )
            if not row:
                raise CVNotFoundError(cv.id)
            row.title = cv.title
            row.context_json = json.loads(cv.context_json)
            row.updated_at = datetime.now(timezone.utc)
            session.flush()
            return _row_to_cv(row)

    def delete(self, cv_id: str, user_id: str) -> None:
        with get_session() as session:
            row = session.scalar(
                select(CVModel).where(
                    CVModel.id == _to_uuid(cv_id),
                    CVModel.user_id == _to_uuid(user_id),
                )
            )
            if not row:
                raise CVNotFoundError(cv_id)
            session.delete(row)
