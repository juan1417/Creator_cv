"""SQLAlchemy models for the Creator CV app.

The app is multi-user: each :class:`CV` belongs to a :class:`User`.
The CV data is stored as JSON text in :attr:`CV.context_json` and
validated with pydantic before persisting.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    cvs = db.relationship(
        "CV",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="CV.updated_at.desc()",
    )

    # --- Password helpers ---
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:  # pragma: no cover - debug only
        return f"<User {self.id} {self.email}>"


class CV(db.Model):
    __tablename__ = "cv"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, default="Mi CV")
    context_json = db.Column(db.Text, nullable=False, default="{}")
    job_offer = db.Column(db.Text, nullable=True)
    review_md = db.Column(db.Text, nullable=True)
    match_score = db.Column(db.Integer, nullable=True)         # 0-100
    match_summary = db.Column(db.Text, nullable=True)          # "3/5 skills · 1/1 idiomas · 4 años"
    match_json = db.Column(db.Text, nullable=True)             # full breakdown
    match_at = db.Column(db.DateTime, nullable=True)           # when the score was computed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # --- JSON helpers ---
    def context_dict(self) -> dict[str, Any]:
        try:
            return json.loads(self.context_json or "{}")
        except (ValueError, TypeError):
            return {}

    def set_context(self, data: dict[str, Any]) -> None:
        self.context_json = json.dumps(data, ensure_ascii=False)

    def __repr__(self) -> str:  # pragma: no cover - debug only
        return f"<CV {self.id} {self.title!r}>"
