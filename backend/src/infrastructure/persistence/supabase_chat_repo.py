"""Implementación Supabase del ChatRepository.

Guardamos los mensajes como JSONB en una sola fila por CV.
Tabla: chat_histories
    id           uuid PRIMARY KEY
    cv_id        uuid NOT NULL REFERENCES cvs(id) ON DELETE CASCADE
    user_id      uuid NOT NULL REFERENCES auth.users(id)
    messages     jsonb NOT NULL DEFAULT '[]'::jsonb
    updated_at   timestamptz NOT NULL DEFAULT now()
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from supabase import Client

from ...domain.entities import ChatMessage
from ...domain.exceptions import CVNotFoundError
from ...domain.repositories import ChatRepository


def _row_to_messages(row: dict) -> list[ChatMessage]:
    raw_msgs = row.get("messages") or []
    out: list[ChatMessage] = []
    for m in raw_msgs:
        out.append(
            ChatMessage(
                role=m["role"],
                content=m["content"],
                patch=m.get("patch"),
                created_at=datetime.fromisoformat(
                    m.get("created_at", row["updated_at"]).replace("Z", "+00:00")
                ),
            )
        )
    return out


def _messages_to_jsonb(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    out = []
    for m in messages:
        out.append(
            {
                "role": m.role,
                "content": m.content,
                "patch": m.patch,
                "created_at": m.created_at.isoformat(),
            }
        )
    return out


class SupabaseChatRepository(ChatRepository):
    def __init__(self, client: Client) -> None:
        self._client = client

    def _get_row(self, cv_id: str, user_id: str) -> dict:
        result = (
            self._client.table("chat_histories")
            .select("*")
            .eq("cv_id", cv_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not result.data:
            raise CVNotFoundError(cv_id)
        return result.data

    def get_messages(self, cv_id: str, user_id: str) -> list[ChatMessage]:
        result = (
            self._client.table("chat_histories")
            .select("messages")
            .eq("cv_id", cv_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not result.data:
            return []
        return _row_to_messages(
            {**(result.data or {}), "updated_at": datetime.utcnow().isoformat()}
        )

    def append(self, cv_id: str, user_id: str, message: ChatMessage) -> None:
        existing = (
            self._client.table("chat_histories")
            .select("messages")
            .eq("cv_id", cv_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        current = (existing.data or {}).get("messages") or []
        current.append(
            {
                "role": message.role,
                "content": message.content,
                "patch": message.patch,
                "created_at": message.created_at.isoformat(),
            }
        )
        if existing.data:
            self._client.table("chat_histories").update(
                {
                    "messages": current,
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                }
            ).eq("cv_id", cv_id).eq("user_id", user_id).execute()
        else:
            self._client.table("chat_histories").insert(
                {"cv_id": cv_id, "user_id": user_id, "messages": current}
            ).execute()

    def clear(self, cv_id: str, user_id: str) -> None:
        self._client.table("chat_histories").update(
            {"messages": [], "updated_at": datetime.utcnow().isoformat() + "Z"}
        ).eq("cv_id", cv_id).eq("user_id", user_id).execute()
