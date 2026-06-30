from __future__ import annotations

import uuid

from sqlalchemy import select, update

from ...domain.entities import BackupCode
from ...domain.repositories import BackupCodeRepository
from .database import get_session
from .models import BackupCodeModel


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _row_to_code(row: BackupCodeModel) -> BackupCode:
    return BackupCode(
        id=str(row.id),
        user_id=str(row.user_id),
        code_hash=row.code_hash,
        used_at=row.used_at,
        created_at=row.created_at,
    )


class SQLAlchemyBackupCodeRepository(BackupCodeRepository):
    def create_many(self, codes: list[BackupCode]) -> list[BackupCode]:
        with get_session() as session:
            models = [
                BackupCodeModel(
                    id=_to_uuid(c.id),
                    user_id=_to_uuid(c.user_id),
                    code_hash=c.code_hash,
                    used_at=c.used_at,
                    created_at=c.created_at,
                )
                for c in codes
            ]
            session.add_all(models)
            session.flush()
            return [_row_to_code(m) for m in models]

    def list_for_user(self, user_id: str) -> list[BackupCode]:
        with get_session() as session:
            rows = session.scalars(
                select(BackupCodeModel).where(
                    BackupCodeModel.user_id == _to_uuid(user_id)
                )
            ).all()
            return [_row_to_code(r) for r in rows]

    def get_by_hash(self, user_id: str, code_hash: str) -> BackupCode | None:
        with get_session() as session:
            row = session.scalar(
                select(BackupCodeModel).where(
                    BackupCodeModel.user_id == _to_uuid(user_id),
                    BackupCodeModel.code_hash == code_hash,
                )
            )
            return _row_to_code(row) if row else None

    def mark_used(self, code_id: str) -> None:
        from datetime import datetime, timezone

        with get_session() as session:
            session.execute(
                update(BackupCodeModel)
                .where(BackupCodeModel.id == _to_uuid(code_id))
                .values(used_at=datetime.now(tz=timezone.utc))
            )

    def delete_all_for_user(self, user_id: str) -> int:
        from sqlalchemy import delete

        with get_session() as session:
            result = session.execute(
                delete(BackupCodeModel).where(
                    BackupCodeModel.user_id == _to_uuid(user_id)
                )
            )
            return result.rowcount or 0
