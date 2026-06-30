"""SQLAlchemy implementation of HistoryRepository."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...domain.repositories import HistoryEntry, HistoryRepository
from .models import HistoryEntryModel


class SQLAlchemyHistoryRepository(HistoryRepository):
    def __init__(self) -> None:
        self._model = HistoryEntryModel

    def _get_session(self) -> Session:
        from .database import get_session

        return next(get_session())

    def _to_entity(self, model: HistoryEntryModel) -> HistoryEntry:
        return HistoryEntry(
            id=str(model.id),
            user_id=str(model.user_id),
            cv_id=str(model.cv_id),
            event_type=model.event_type,
            title=model.title,
            description=model.description,
            snapshot=model.snapshot,
            created_at=model.created_at,
        )

    def create(self, entry: HistoryEntry) -> HistoryEntry:
        session = self._get_session()
        try:
            model = self._model(
                id=entry.id,
                user_id=entry.user_id,
                cv_id=entry.cv_id,
                event_type=entry.event_type,
                title=entry.title,
                description=entry.description,
                snapshot=entry.snapshot,
                created_at=entry.created_at or datetime.now(timezone.utc),
            )
            session.add(model)
            session.commit()
            return self._to_entity(model)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_for_user(
        self, user_id: str, cv_id: str | None = None, event_type: str | None = None
    ) -> list[HistoryEntry]:
        session = self._get_session()
        try:
            stmt = select(self._model).where(self._model.user_id == user_id)
            if cv_id:
                stmt = stmt.where(self._model.cv_id == cv_id)
            if event_type:
                stmt = stmt.where(self._model.event_type == event_type)
            stmt = stmt.order_by(self._model.created_at.desc()).limit(100)
            rows = session.execute(stmt).scalars().all()
            return [self._to_entity(r) for r in rows]
        finally:
            session.close()

    def get_by_id(self, entry_id: str, user_id: str) -> HistoryEntry | None:
        session = self._get_session()
        try:
            stmt = select(self._model).where(
                self._model.id == entry_id, self._model.user_id == user_id
            )
            model = session.execute(stmt).scalar_one_or_none()
            return self._to_entity(model) if model else None
        finally:
            session.close()

    def delete_for_cv(self, cv_id: str) -> int:
        session = self._get_session()
        try:
            stmt = delete(self._model).where(self._model.cv_id == cv_id)
            result = session.execute(stmt)
            session.commit()
            return result.rowcount or 0
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
