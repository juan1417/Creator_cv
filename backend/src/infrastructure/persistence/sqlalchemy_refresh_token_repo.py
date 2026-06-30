from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update

from ...domain.entities import RefreshToken
from ...domain.repositories import RefreshTokenRepository
from .database import get_session
from .models import RefreshTokenModel


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _row_to_token(row: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=str(row.id),
        user_id=str(row.user_id),
        token_hash=row.token_hash,
        family_id=str(row.family_id),
        expires_at=row.expires_at,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
        replaced_by_id=str(row.replaced_by_id) if row.replaced_by_id else None,
    )


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def create(self, token: RefreshToken) -> RefreshToken:
        with get_session() as session:
            model = RefreshTokenModel(
                id=_to_uuid(token.id),
                user_id=_to_uuid(token.user_id),
                token_hash=token.token_hash,
                family_id=_to_uuid(token.family_id),
                expires_at=token.expires_at,
                created_at=token.created_at,
                revoked_at=token.revoked_at,
                replaced_by_id=(
                    _to_uuid(token.replaced_by_id) if token.replaced_by_id else None
                ),
            )
            session.add(model)
            session.flush()
            return _row_to_token(model)

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        with get_session() as session:
            row = session.scalar(
                select(RefreshTokenModel).where(
                    RefreshTokenModel.token_hash == token_hash
                )
            )
            return _row_to_token(row) if row else None

    def mark_revoked(
        self, token_id: str, replaced_by_id: str | None = None
    ) -> None:
        with get_session() as session:
            session.execute(
                update(RefreshTokenModel)
                .where(RefreshTokenModel.id == _to_uuid(token_id))
                .values(
                    revoked_at=datetime.now(tz=__import__("datetime").timezone.utc),
                    replaced_by_id=(
                        _to_uuid(replaced_by_id) if replaced_by_id else None
                    ),
                )
            )

    def revoke_family(self, family_id: str) -> int:
        with get_session() as session:
            from datetime import timezone

            result = session.execute(
                update(RefreshTokenModel)
                .where(
                    RefreshTokenModel.family_id == _to_uuid(family_id),
                    RefreshTokenModel.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.now(tz=timezone.utc))
            )
            return result.rowcount or 0

    def revoke_all_for_user(self, user_id: str) -> int:
        with get_session() as session:
            from datetime import timezone

            result = session.execute(
                update(RefreshTokenModel)
                .where(
                    RefreshTokenModel.user_id == _to_uuid(user_id),
                    RefreshTokenModel.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.now(tz=timezone.utc))
            )
            return result.rowcount or 0
