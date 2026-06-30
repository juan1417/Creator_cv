"""Inputs de los use cases: dataclasses frozen con normalización."""
from __future__ import annotations

from dataclasses import dataclass

from ..domain.exceptions import ValidationError


def _strip_title(v: str) -> str:
    v = (v or "").strip()
    if not v:
        raise ValidationError("title", "El título no puede estar vacío")
    return v


@dataclass(frozen=True)
class CreateCVInput:
    title: str
    context_json: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _strip_title(self.title))


@dataclass(frozen=True)
class GetCVInput:
    cv_id: str


@dataclass(frozen=True)
class ListCVsInput:
    pass


@dataclass(frozen=True)
class UpdateCVInput:
    cv_id: str
    title: str | None = None
    context_json: str | None = None

    def __post_init__(self) -> None:
        if self.title is not None:
            object.__setattr__(self, "title", _strip_title(self.title))


@dataclass(frozen=True)
class DeleteCVInput:
    cv_id: str


@dataclass(frozen=True)
class AppendChatInput:
    role: str
    content: str
    patch: dict | None = None
