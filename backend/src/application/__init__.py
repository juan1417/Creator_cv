"""Application layer: casos de uso (orquestación del dominio).

Los use cases NO saben nada de Flask, Supabase, ni HTTP.
Solo orquestan entidades y repositorios.

Cada use case es una clase con un método `execute()`.
Recibe dependencias por constructor (DI).
"""
from .use_cases import (
    CreateCV,
    UpdateCV,
    GetCV,
    ListCVs,
    DeleteCV,
    DuplicateCV,
    GetChat,
    AppendChat,
    ClearChat,
)
from .dto import (
    CreateCVRequest,
    UpdateCVRequest,
    CVResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    CompareRequest,
    ChatAIRequest,
)

__all__ = [
    "CreateCV",
    "UpdateCV",
    "GetCV",
    "ListCVs",
    "DeleteCV",
    "DuplicateCV",
    "GetChat",
    "AppendChat",
    "ClearChat",
    "CreateCVRequest",
    "UpdateCVRequest",
    "CVResponse",
    "ChatMessageRequest",
    "ChatMessageResponse",
    "ChatAIRequest",
]
