from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from ...domain.entities import ChatMessage
from ...domain.repositories import ChatRepository
from .database import get_session
from .models import ChatHistoryModel


def _messages_to_objects(raw_json: str) -> list[ChatMessage]:
    data = json.loads(raw_json) if raw_json else []
    out: list[ChatMessage] = []
    for m in data:
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


def _messages_to_json(messages: list[ChatMessage]) -> str:
    out: list[dict[str, Any]] = []
    for m in messages:
        out.append(
            {
                "role": m.role,
                "content": m.content,
                "patch": m.patch,
                "created_at": m.created_at.isoformat(),
            }
        )
    return json.dumps(out, ensure_ascii=False)


class SQLAlchemyChatRepository(ChatRepository):
    def get_messages(self, cv_id: str, user_id: str) -> list[ChatMessage]:
        with get_session() as session:
            row = session.scalar(
                select(ChatHistoryModel).where(
                    ChatHistoryModel.cv_id == cv_id,
                    ChatHistoryModel.user_id == user_id,
                )
            )
            if not row:
                return []
            return _messages_to_objects(row.messages)

    def append(self, cv_id: str, user_id: str, message: ChatMessage) -> None:
        with get_session() as session:
            row = session.scalar(
                select(ChatHistoryModel).where(
                    ChatHistoryModel.cv_id == cv_id,
                    ChatHistoryModel.user_id == user_id,
                )
            )
            now = datetime.now(timezone.utc)
            if row:
                msgs = _messages_to_objects(row.messages)
                msgs.append(message)
                row.messages = _messages_to_json(msgs)
                row.updated_at = now
            else:
                session.add(
                    ChatHistoryModel(
                        cv_id=cv_id,
                        user_id=user_id,
                        messages=_messages_to_json([message]),
                    )
                )

    def clear(self, cv_id: str, user_id: str) -> None:
        with get_session() as session:
            row = session.scalar(
                select(ChatHistoryModel).where(
                    ChatHistoryModel.cv_id == cv_id,
                    ChatHistoryModel.user_id == user_id,
                )
            )
            if row:
                row.messages = "[]"
                row.updated_at = datetime.now(timezone.utc)
