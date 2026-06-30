"""Domain layer: entidades, value objects, y excepciones del dominio.

Este layer NO tiene dependencias de frameworks (Flask, Supabase, etc).
Es Python puro que representa el negocio.
"""

from .entities import CV, ChatMessage
from .value_objects import CVContext, ContactInfo
from .exceptions import (
    CVNotFoundError,
    ChatNotFoundError,
    UnauthorizedError,
    ValidationError,
)
from .repositories import CVRepository, ChatRepository

__all__ = [
    "CV",
    "ChatMessage",
    "CVContext",
    "ContactInfo",
    "CVNotFoundError",
    "ChatNotFoundError",
    "UnauthorizedError",
    "ValidationError",
    "CVRepository",
    "ChatRepository",
]
