"""Tests unitarios de los use cases con un repositorio en memoria."""
from __future__ import annotations

from datetime import datetime
from typing import Sequence

import pytest

from src.application.use_cases import (
    AppendChat,
    ClearChat,
    CreateCV,
    DeleteCV,
    GetCV,
    GetChat,
    ListCVs,
    UpdateCV,
)
from src.application.inputs import (
    CreateCVInput,
    DeleteCVInput,
    GetCVInput,
    ListCVsInput,
    UpdateCVInput,
)
from src.domain.entities import CV, ChatMessage
from src.domain.exceptions import CVNotFoundError, ValidationError
from src.domain.repositories import CVRepository, ChatRepository


class InMemoryCVRepo(CVRepository):
    def __init__(self) -> None:
        self._items: dict[str, CV] = {}

    def create(self, cv: CV) -> CV:
        cv.id = f"cv-{len(self._items) + 1}"
        self._items[cv.id] = cv
        return cv

    def get(self, cv_id: str, user_id: str) -> CV:
        cv = self._items.get(cv_id)
        if not cv or cv.user_id != user_id:
            raise CVNotFoundError(cv_id)
        return cv

    def list_for_user(self, user_id: str) -> Sequence[CV]:
        return [cv for cv in self._items.values() if cv.user_id == user_id]

    def update(self, cv: CV) -> CV:
        self._items[cv.id] = cv
        return cv

    def delete(self, cv_id: str, user_id: str) -> None:
        cv = self.get(cv_id, user_id)
        del self._items[cv_id]


class InMemoryChatRepo(ChatRepository):
    def __init__(self) -> None:
        self._items: dict[str, list[ChatMessage]] = {}

    def get_messages(self, cv_id: str, user_id: str) -> list[ChatMessage]:
        return list(self._items.get(cv_id, []))

    def append(self, cv_id: str, user_id: str, message: ChatMessage) -> None:
        self._items.setdefault(cv_id, []).append(message)

    def clear(self, cv_id: str, user_id: str) -> None:
        self._items[cv_id] = []


@pytest.fixture
def cv_repo():
    return InMemoryCVRepo()


@pytest.fixture
def chat_repo():
    return InMemoryChatRepo()


def test_create_cv_with_empty_context(cv_repo):
    use_case = CreateCV(cv_repo)
    result = use_case.execute("user-1", CreateCVInput(title="Mi CV"))
    assert result.id == "cv-1"
    assert result.title == "Mi CV"
    assert "meta" in result.context_json


def test_create_cv_strips_title(cv_repo):
    use_case = CreateCV(cv_repo)
    result = use_case.execute("user-1", CreateCVInput(title="  Hola  "))
    assert result.title == "Hola"


def test_create_cv_rejects_empty_title(cv_repo):
    use_case = CreateCV(cv_repo)
    with pytest.raises(ValidationError):
        use_case.execute("user-1", CreateCVInput(title="   "))


def test_list_cvs_filters_by_user(cv_repo):
    CreateCV(cv_repo).execute("user-1", CreateCVInput(title="A"))
    CreateCV(cv_repo).execute("user-1", CreateCVInput(title="B"))
    CreateCV(cv_repo).execute("user-2", CreateCVInput(title="C"))

    result = ListCVs(cv_repo).execute("user-1", ListCVsInput())
    assert len(result) == 2
    titles = {c.title for c in result}
    assert titles == {"A", "B"}


def test_update_cv_title(cv_repo):
    create = CreateCV(cv_repo)
    update = UpdateCV(cv_repo)
    cv = create.execute("user-1", CreateCVInput(title="Original"))
    updated = update.execute("user-1", UpdateCVInput(cv_id=cv.id, title="Nuevo"))
    assert updated.title == "Nuevo"


def test_update_cv_rejects_invalid_json(cv_repo):
    create = CreateCV(cv_repo)
    update = UpdateCV(cv_repo)
    cv = create.execute("user-1", CreateCVInput(title="X"))
    with pytest.raises(ValidationError):
        update.execute("user-1", UpdateCVInput(cv_id=cv.id, context_json="not json"))


def test_get_cv_from_other_user_raises(cv_repo):
    create = CreateCV(cv_repo)
    get = GetCV(cv_repo)
    cv = create.execute("user-1", CreateCVInput(title="X"))
    with pytest.raises(CVNotFoundError):
        get.execute("user-2", GetCVInput(cv_id=cv.id))


def test_delete_cv(cv_repo):
    create = CreateCV(cv_repo)
    delete = DeleteCV(cv_repo)
    cv = create.execute("user-1", CreateCVInput(title="X"))
    delete.execute("user-1", DeleteCVInput(cv_id=cv.id))
    with pytest.raises(CVNotFoundError):
        GetCV(cv_repo).execute("user-1", GetCVInput(cv_id=cv.id))


def test_chat_append_and_get(chat_repo):
    append = AppendChat(chat_repo)
    get = GetChat(chat_repo)
    append.execute("user-1", "cv-1", "user", "Hola", None)
    append.execute("user-1", "cv-1", "assistant", "Hola, ¿en qué te ayudo?", None)
    msgs = get.execute("user-1", "cv-1")
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[1].role == "assistant"


def test_chat_clear(chat_repo):
    append = AppendChat(chat_repo)
    clear = ClearChat(chat_repo)
    get = GetChat(chat_repo)
    append.execute("user-1", "cv-1", "user", "Hola", None)
    clear.execute("user-1", "cv-1")
    assert get.execute("user-1", "cv-1") == []
