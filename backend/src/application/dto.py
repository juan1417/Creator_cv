"""DTOs (Data Transfer Objects): contratos de entrada/salida de los use cases.

Usamos Pydantic para validación automática.
Los DTOs NO son entidades — son solo shapes para la API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateCVRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    context_json: str | None = None  # si None, se genera uno vacío

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El título no puede estar vacío")
        return v


class UpdateCVRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    context_json: str | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("El título no puede estar vacío")
        return v

    def has_any(self) -> bool:
        return self.title is not None or self.context_json is not None


class CVResponse(BaseModel):
    id: str
    title: str
    context_json: str
    created_at: datetime
    updated_at: datetime


class ChatMessageRequest(BaseModel):
    role: str  # "user" | "assistant"
    content: str = Field(min_length=1)
    patch: dict[str, Any] | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("role debe ser 'user' o 'assistant'")
        return v


class ChatMessageResponse(BaseModel):
    role: str
    content: str
    patch: dict[str, Any] | None = None
    created_at: datetime
