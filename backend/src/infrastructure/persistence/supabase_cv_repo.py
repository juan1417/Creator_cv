"""Implementación Supabase del CVRepository.

Tabla: cvs
    id            uuid PRIMARY KEY
    user_id       uuid NOT NULL REFERENCES auth.users(id)
    title         text NOT NULL
    context_json  text NOT NULL
    created_at    timestamptz NOT NULL DEFAULT now()
    updated_at    timestamptz NOT NULL DEFAULT now()
"""
from __future__ import annotations

from datetime import datetime
from typing import Sequence

from supabase import Client

from ...domain.entities import CV
from ...domain.exceptions import CVNotFoundError
from ...domain.repositories import CVRepository


def _row_to_cv(row: dict) -> CV:
    return CV(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        context_json=row["context_json"],
        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
    )


class SupabaseCVRepository(CVRepository):
    def __init__(self, client: Client) -> None:
        self._client = client

    def create(self, cv: CV) -> CV:
        result = (
            self._client.table("cvs")
            .insert(
                {
                    "user_id": cv.user_id,
                    "title": cv.title,
                    "context_json": cv.context_json,
                }
            )
            .execute()
        )
        return _row_to_cv(result.data[0])

    def get(self, cv_id: str, user_id: str) -> CV:
        result = (
            self._client.table("cvs")
            .select("*")
            .eq("id", cv_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not result.data:
            raise CVNotFoundError(cv_id)
        return _row_to_cv(result.data)

    def list_for_user(self, user_id: str) -> Sequence[CV]:
        result = (
            self._client.table("cvs")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return [_row_to_cv(r) for r in result.data]

    def update(self, cv: CV) -> CV:
        result = (
            self._client.table("cvs")
            .update(
                {
                    "title": cv.title,
                    "context_json": cv.context_json,
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                }
            )
            .eq("id", cv.id)
            .eq("user_id", cv.user_id)
            .execute()
        )
        if not result.data:
            raise CVNotFoundError(cv.id)
        return _row_to_cv(result.data[0])

    def delete(self, cv_id: str, user_id: str) -> None:
        result = (
            self._client.table("cvs")
            .delete()
            .eq("id", cv_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not result.data:
            raise CVNotFoundError(cv_id)
