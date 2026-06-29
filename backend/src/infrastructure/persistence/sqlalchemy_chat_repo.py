from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from ...domain.entities import ChatMessage
from ...domain.repositories import ChatRepository
from .database import get_session
from .models import ChatHistoryModel


def _to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _messages_to_objects(raw: list[dict[str, Any]] | None) -> list[ChatMessage]:
    """Convierte la lista cruda (JSONB → ``list[dict]``) a entidades de dominio."""
    if not raw:
        return []
    out: list[ChatMessage] = []
    for m in raw:
        out.append(
            ChatMessage(
                role=m["role"],
                content=m["content"],
                patch=m.get("patch"),
                created_at=datetime.fromisoformat(
                    m.get("created_at", datetime.now(timezone.utc).isoformat())
                ),
            )
        )
    return out


def _messages_from_objects(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    """Serializa entidades a la estructura que se persiste en JSONB."""
    return [
        {
            "role": m.role,
            "content": m.content,
            "patch": m.patch,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


class SQLAlchemyChatRepository(ChatRepository):
    def get_messages(self, cv_id: str, user_id: str) -> list[ChatMessage]:
        with get_session() as session:
            row = session.scalar(
                select(ChatHistoryModel).where(
                    ChatHistoryModel.cv_id == _to_uuid(cv_id),
                    ChatHistoryModel.user_id == _to_uuid(user_id),
                )
            )
            if not row:
                return []
            return _messages_to_objects(row.messages)

    def append(self, cv_id: str, user_id: str, message: ChatMessage) -> None:
        with get_session() as session:
            row = session.scalar(
                select(ChatHistoryModel).where(
                    ChatHistoryModel.cv_id == _to_uuid(cv_id),
                    ChatHistoryModel.user_id == _to_uuid(user_id),
                )
            )
            now = datetime.now(timezone.utc)
            if row:
                msgs = _messages_to_objects(row.messages)
                msgs.append(message)
                row.messages = _messages_from_objects(msgs)
                row.updated_at = now
            else:
                session.add(
                    ChatHistoryModel(
                        cv_id=_to_uuid(cv_id),
                        user_id=_to_uuid(user_id),
                        messages=_messages_from_objects([message]),
                    )
                )

    def clear(self, cv_id: str, user_id: str) -> None:
        with get_session() as session:
            row = session.scalar(
                select(ChatHistoryModel).where(
                    ChatHistoryModel.cv_id == _to_uuid(cv_id),
                    ChatHistoryModel.user_id == _to_uuid(user_id),
                )
            )
            if row:
                row.messages = []
                row.updated_at = datetime.now(timezone.utc)
