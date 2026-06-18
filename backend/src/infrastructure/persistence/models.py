import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_new_uuid)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    cvs = relationship("CVModel", back_populates="user", cascade="all, delete-orphan")


class CVModel(Base):
    __tablename__ = "cvs"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    context_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    user = relationship("UserModel", back_populates="cvs")
    chat_histories = relationship(
        "ChatHistoryModel", back_populates="cv", cascade="all, delete-orphan"
    )


class ChatHistoryModel(Base):
    __tablename__ = "chat_histories"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_new_uuid)
    cv_id: Mapped[str] = mapped_column(
        Text, ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id"), nullable=False
    )
    messages: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # JSON array
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    cv = relationship("CVModel", back_populates="chat_histories")
