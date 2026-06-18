"""Entidades del dominio: objetos con identidad propia.

Una entidad se identifica por su ID (no por sus atributos).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CV:
    """Un CV pertenece a un usuario y tiene un contexto JSON (estructura libre)."""

    id: str
    user_id: str
    title: str
    context_json: str  # JSON serializado del contexto completo
    created_at: datetime
    updated_at: datetime

    def update_title(self, new_title: str) -> None:
        if not new_title or not new_title.strip():
            raise ValueError("El título no puede estar vacío")
        self.title = new_title.strip()
        self.updated_at = datetime.utcnow()

    def update_context(self, new_context_json: str) -> None:
        if not new_context_json or not new_context_json.strip():
            raise ValueError("El contexto no puede estar vacío")
        self.context_json = new_context_json
        self.updated_at = datetime.utcnow()


@dataclass
class ChatMessage:
    """Un mensaje de chat (user o assistant) con contenido y opcional patch JSON."""

    role: str  # "user" | "assistant"
    content: str
    patch: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.role not in ("user", "assistant"):
            raise ValueError(f"role debe ser 'user' o 'assistant', recibí {self.role!r}")
        if not self.content or not self.content.strip():
            raise ValueError("content no puede estar vacío")
