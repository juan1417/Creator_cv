"""Repository interfaces: contratos que la infrastructure debe implementar.

El dominio define QUÉ se puede hacer con los datos, no CÓMO.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from .entities import CV, ChatMessage


class CVRepository(ABC):
    """Contrato para persistir CVs. El user_id es el dueño."""

    @abstractmethod
    def create(self, cv: CV) -> CV:
        """Crea un CV y lo persiste. Devuelve el CV con su id."""
        ...

    @abstractmethod
    def get(self, cv_id: str, user_id: str) -> CV:
        """Obtiene un CV por id. Lanza CVNotFoundError si no existe
        o no pertenece al usuario."""
        ...

    @abstractmethod
    def list_for_user(self, user_id: str) -> Sequence[CV]:
        """Lista todos los CVs de un usuario, ordenados por updated_at desc."""
        ...

    @abstractmethod
    def update(self, cv: CV) -> CV:
        """Actualiza un CV existente. Asume que ya fue validado por el caller."""
        ...

    @abstractmethod
    def delete(self, cv_id: str, user_id: str) -> None:
        """Elimina un CV. Lanza CVNotFoundError si no existe o no pertenece al user."""
        ...


class ChatRepository(ABC):
    """Contrato para persistir el historial de chat de un CV."""

    @abstractmethod
    def get_messages(self, cv_id: str, user_id: str) -> list[ChatMessage]:
        """Devuelve los mensajes del chat. Lista vacía si no hay."""
        ...

    @abstractmethod
    def append(self, cv_id: str, user_id: str, message: ChatMessage) -> None:
        """Agrega un mensaje al final del chat."""
        ...

    @abstractmethod
    def clear(self, cv_id: str, user_id: str) -> None:
        """Limpia todo el historial del chat."""
        ...
