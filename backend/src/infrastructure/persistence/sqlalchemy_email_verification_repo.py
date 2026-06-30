from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select

from ...domain.entities import EmailVerificationToken
from ...domain.repositories import EmailVerificationTokenRepository
from .database import get_session
from .models import EmailVerificationTokenModel


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _row_to_token(row: EmailVerificationTokenModel) -> EmailVerificationToken:
    return EmailVerificationToken(
        id=str(row.id),
        user_id=str(row.user_id),
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


class SQLAlchemyEmailVerificationTokenRepository(EmailVerificationTokenRepository):
    def create(self, token: EmailVerificationToken) -> EmailVerificationToken:
        with get_session() as session:
            model = EmailVerificationTokenModel(
                id=_to_uuid(token.id),
                user_id=_to_uuid(token.user_id),
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                created_at=token.created_at,
            )
            session.add(model)
            session.flush()
            return _row_to_token(model)

    def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        with get_session() as session:
            row = session.scalar(
                select(EmailVerificationTokenModel).where(
                    EmailVerificationTokenModel.token_hash == token_hash
                )
            )
            return _row_to_token(row) if row else None

    def delete(self, token_id: str) -> None:
        with get_session() as session:
            session.execute(
                delete(EmailVerificationTokenModel).where(
                    EmailVerificationTokenModel.id == _to_uuid(token_id)
                )
            )

    def delete_for_user(self, user_id: str) -> int:
        with get_session() as session:
            result = session.execute(
                delete(EmailVerificationTokenModel).where(
                    EmailVerificationTokenModel.user_id == _to_uuid(user_id)
                )
            )
            return result.rowcount or 0
