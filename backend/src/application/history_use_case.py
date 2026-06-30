"""History use cases: record and query CV change history."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from ..domain.repositories import HistoryEntry, HistoryRepository


@dataclass
class HistoryEntryOutput:
    id: str
    cv_id: str
    event_type: str
    title: str
    description: str
    snapshot: dict | None
    created_at: str


def _to_output(entry: HistoryEntry) -> HistoryEntryOutput:
    return HistoryEntryOutput(
        id=entry.id,
        cv_id=entry.cv_id,
        event_type=entry.event_type,
        title=entry.title,
        description=entry.description,
        snapshot=entry.snapshot,
        created_at=entry.created_at.isoformat() if entry.created_at else "",
    )


class RecordHistoryEntry:
    def __init__(self, history_repo: HistoryRepository) -> None:
        self._repo = history_repo

    def execute(
        self,
        user_id: str,
        cv_id: str,
        event_type: str,
        title: str,
        description: str = "",
        snapshot: dict | None = None,
    ) -> HistoryEntryOutput:
        entry = HistoryEntry(
            id=str(uuid.uuid4()),
            user_id=user_id,
            cv_id=cv_id,
            event_type=event_type,
            title=title,
            description=description,
            snapshot=snapshot,
            created_at=datetime.now(timezone.utc),
        )
        saved = self._repo.create(entry)
        return _to_output(saved)


class GetCVHistory:
    def __init__(self, history_repo: HistoryRepository) -> None:
        self._repo = history_repo

    def execute(
        self, user_id: str, cv_id: str | None = None, event_type: str | None = None
    ) -> list[HistoryEntryOutput]:
        entries = self._repo.list_for_user(user_id, cv_id=cv_id, event_type=event_type)
        return [_to_output(e) for e in entries]


class RestoreSnapshot:
    def __init__(self, history_repo: HistoryRepository) -> None:
        self._repo = history_repo

    def execute(self, user_id: str, entry_id: str) -> dict | None:
        entry = self._repo.get_by_id(entry_id, user_id)
        if entry is None or entry.snapshot is None:
            return None
        return entry.snapshot
