from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from creator_cv.extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    cvs: Mapped[list[CV]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CV(db.Model):
    __tablename__ = "cvs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), default="")
    context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat_history_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    user: Mapped[User] = relationship(back_populates="cvs")
    sections: Mapped[list[CvSection]] = relationship(
        back_populates="cv",
        cascade="all, delete-orphan",
        order_by="CvSection.sort_order",
        passive_deletes=True,
    )


class CvSection(db.Model):
    __tablename__ = "cv_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    cv_id: Mapped[int] = mapped_column(
        ForeignKey("cvs.id", ondelete="CASCADE"),
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    key: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    cv: Mapped[CV] = relationship(back_populates="sections")
