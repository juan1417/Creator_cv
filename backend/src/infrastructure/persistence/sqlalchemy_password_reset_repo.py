from __future__ import annotations

import uuid

from sqlalchemy import delete, select

from ...domain.entities import PasswordResetToken
from ...domain.repositories import PasswordResetTokenRepository
from .database import get_session
from .models import PasswordResetTokenModel


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _row_to_token(row: PasswordResetTokenModel) -> PasswordResetToken:
    return PasswordResetToken(
        id=str(row.id),
        user_id=str(row.user_id),
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


class SQLAlchemyPasswordResetTokenRepository(PasswordResetTokenRepository):
    def create(self, token: PasswordResetToken) -> PasswordResetToken:
        with get_session() as session:
            model = PasswordResetTokenModel(
                id=_to_uuid(token.id),
                user_id=_to_uuid(token.user_id),
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                created_at=token.created_at,
            )
            session.add(model)
            session.flush()
            return _row_to_token(model)

    def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        with get_session() as session:
            row = session.scalar(
                select(PasswordResetTokenModel).where(
                    PasswordResetTokenModel.token_hash == token_hash
                )
            )
            return _row_to_token(row) if row else None

    def delete(self, token_id: str) -> None:
        with get_session() as session:
            session.execute(
                delete(PasswordResetTokenModel).where(
                    PasswordResetTokenModel.id == _to_uuid(token_id)
                )
            )

    def delete_for_user(self, user_id: str) -> int:
        with get_session() as session:
            result = session.execute(
                delete(PasswordResetTokenModel).where(
                    PasswordResetTokenModel.user_id == _to_uuid(user_id)
                )
            )
            return result.rowcount or 0
