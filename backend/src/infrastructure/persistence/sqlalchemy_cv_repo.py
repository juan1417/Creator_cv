from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update

from ...domain.entities import CV
from ...domain.exceptions import CVNotFoundError
from ...domain.repositories import CVRepository
from .database import get_session
from .models import CVModel


def _row_to_cv(row: CVModel) -> CV:
    return CV(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        context_json=row.context_json,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyCVRepository(CVRepository):
    def create(self, cv: CV) -> CV:
        with get_session() as session:
            kwargs = dict(
                user_id=cv.user_id,
                title=cv.title,
                context_json=cv.context_json,
            )
            if cv.id:
                kwargs["id"] = cv.id
            model = CVModel(**kwargs)
            session.add(model)
            session.flush()
            return _row_to_cv(model)

    def get(self, cv_id: str, user_id: str) -> CV:
        with get_session() as session:
            row = session.scalar(
                select(CVModel).where(CVModel.id == cv_id, CVModel.user_id == user_id)
            )
            if not row:
                raise CVNotFoundError(cv_id)
            return _row_to_cv(row)

    def list_for_user(self, user_id: str) -> Sequence[CV]:
        with get_session() as session:
            rows = session.scalars(
                select(CVModel)
                .where(CVModel.user_id == user_id)
                .order_by(CVModel.updated_at.desc())
            ).all()
            return [_row_to_cv(r) for r in rows]

    def update(self, cv: CV) -> CV:
        with get_session() as session:
            row = session.scalar(
                select(CVModel).where(CVModel.id == cv.id, CVModel.user_id == cv.user_id)
            )
            if not row:
                raise CVNotFoundError(cv.id)
            row.title = cv.title
            row.context_json = cv.context_json
            row.updated_at = datetime.now(timezone.utc)
            session.flush()
            return _row_to_cv(row)

    def delete(self, cv_id: str, user_id: str) -> None:
        with get_session() as session:
            row = session.scalar(
                select(CVModel).where(CVModel.id == cv_id, CVModel.user_id == user_id)
            )
            if not row:
                raise CVNotFoundError(cv_id)
            session.delete(row)
