from __future__ import annotations

import uuid

from sqlalchemy import select

from ...domain.entities import User
from ...domain.exceptions import UserAlreadyExistsError
from ...domain.repositories import UserRepository
from .database import get_session
from .models import UserModel


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _row_to_user(row: UserModel) -> User:
    return User(
        id=str(row.id),
        email=row.email,
        password_hash=row.password_hash,
        email_verified=row.email_verified,
        email_verified_at=row.email_verified_at,
        created_at=row.created_at,
        totp_enabled=row.totp_enabled,
        totp_secret_encrypted=row.totp_secret_encrypted,
        totp_enabled_at=row.totp_enabled_at,
    )


class SQLAlchemyUserRepository(UserRepository):
    def get_by_id(self, user_id: str) -> User | None:
        with get_session() as session:
            row = session.scalar(
                select(UserModel).where(UserModel.id == _to_uuid(user_id))
            )
            return _row_to_user(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        with get_session() as session:
            row = session.scalar(
                select(UserModel).where(UserModel.email == email.strip().lower())
            )
            return _row_to_user(row) if row else None

    def create(self, user: User) -> User:
        with get_session() as session:
            existing = session.scalar(
                select(UserModel).where(UserModel.email == user.email)
            )
            if existing:
                raise UserAlreadyExistsError(user.email)
            model = UserModel(
                id=_to_uuid(user.id),
                email=user.email,
                password_hash=user.password_hash,
                email_verified=user.email_verified,
                email_verified_at=user.email_verified_at,
                created_at=user.created_at,
                totp_enabled=user.totp_enabled,
                totp_secret_encrypted=user.totp_secret_encrypted,
                totp_enabled_at=user.totp_enabled_at,
            )
            session.add(model)
            session.flush()
            return _row_to_user(model)

    def update(self, user: User) -> User:
        with get_session() as session:
            row = session.scalar(
                select(UserModel).where(UserModel.id == _to_uuid(user.id))
            )
            if not row:
                raise UserAlreadyExistsError(user.email)
            row.email = user.email
            row.password_hash = user.password_hash
            row.email_verified = user.email_verified
            row.email_verified_at = user.email_verified_at
            row.totp_enabled = user.totp_enabled
            row.totp_secret_encrypted = user.totp_secret_encrypted
            row.totp_enabled_at = user.totp_enabled_at
            session.flush()
            return _row_to_user(row)
