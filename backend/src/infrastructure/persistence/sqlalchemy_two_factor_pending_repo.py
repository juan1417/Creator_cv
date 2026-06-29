from __future__ import annotations

import uuid

from sqlalchemy import delete, select

from ...domain.entities import TwoFactorPending
from ...domain.repositories import TwoFactorPendingRepository
from .database import get_session
from .models import TwoFactorPendingModel


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _row_to_pending(row: TwoFactorPendingModel) -> TwoFactorPending:
    return TwoFactorPending(
        id=str(row.id),
        user_id=str(row.user_id),
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


class SQLAlchemyTwoFactorPendingRepository(TwoFactorPendingRepository):
    def create(self, pending: TwoFactorPending) -> TwoFactorPending:
        with get_session() as session:
            model = TwoFactorPendingModel(
                id=_to_uuid(pending.id),
                user_id=_to_uuid(pending.user_id),
                token_hash=pending.token_hash,
                expires_at=pending.expires_at,
                created_at=pending.created_at,
            )
            session.add(model)
            session.flush()
            return _row_to_pending(model)

    def get_by_hash(self, token_hash: str) -> TwoFactorPending | None:
        with get_session() as session:
            row = session.scalar(
                select(TwoFactorPendingModel).where(
                    TwoFactorPendingModel.token_hash == token_hash
                )
            )
            return _row_to_pending(row) if row else None

    def delete(self, pending_id: str) -> None:
        with get_session() as session:
            session.execute(
                delete(TwoFactorPendingModel).where(
                    TwoFactorPendingModel.id == _to_uuid(pending_id)
                )
            )

    def delete_for_user(self, user_id: str) -> int:
        with get_session() as session:
            result = session.execute(
                delete(TwoFactorPendingModel).where(
                    TwoFactorPendingModel.user_id == _to_uuid(user_id)
                )
            )
            return result.rowcount or 0
