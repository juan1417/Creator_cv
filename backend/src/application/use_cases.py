"""Use cases: lógica de aplicación.

Cada use case es una clase con un único método `execute()`.
Las dependencias se inyectan por constructor (no globales).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Sequence

from ..domain.entities import CV, ChatMessage
from ..domain.exceptions import CVNotFoundError, ChatNotFoundError, ValidationError
from ..domain.repositories import CVRepository, ChatRepository
from .dto import (
    CVResponse,
    CreateCVRequest,
    UpdateCVRequest,
    ChatMessageRequest,
    ChatMessageResponse,
)
from .inputs import (
    CreateCVInput,
    DeleteCVInput,
    GetCVInput,
    ListCVsInput,
    UpdateCVInput,
    AppendChatInput,
)


def _cv_to_response(cv: CV) -> CVResponse:
    return CVResponse(
        id=cv.id,
        title=cv.title,
        context_json=cv.context_json,
        created_at=cv.created_at,
        updated_at=cv.updated_at,
    )


def _empty_context_json() -> str:
    return json.dumps(
        {
            "meta": {
                "nombre_completo": "",
                "titulo_profesional": "",
                "idioma_cv": "español",
                "objetivo_cv": "",
                "tipo_cv": "",
                "nivel_seniority": "",
                "contacto": {
                    "telefono": "",
                    "email": "",
                    "linkedin": "",
                    "ubicacion": "",
                },
            },
            "certificaciones": [],
            "fortalezas": [],
            "perfil_profesional": {"resumen": "", "palabras_clave": []},
            "experiencia": [],
            "educacion": [],
            "habilidades": {"tecnicas": [], "blandas": [], "idiomas": []},
            "proyectos": [],
            "recursos_actuales": {"cv_existente": False, "texto_cv": "", "links": []},
            "restricciones": {
                "extension_maxima_paginas": 1,
                "formato_solicitado": "PDF",
                "otro": "",
            },
            "dudas_pendientes": [],
        },
        ensure_ascii=False,
        indent=2,
    )


def _validate_context_json(raw: str) -> str:
    """Valida que el JSON sea parseable y re-emite normalizado."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValidationError("context_json", f"JSON inválido: {e}")
    if not isinstance(data, dict):
        raise ValidationError("context_json", "Debe ser un objeto JSON de nivel superior")
    return json.dumps(data, ensure_ascii=False, indent=2)


class CreateCV:
    def __init__(self, cv_repo: CVRepository) -> None:
        self._repo = cv_repo

    def execute(self, user_id: str, input: CreateCVInput) -> CVResponse:
        context = input.context_json.strip() if input.context_json else ""
        if not context:
            context = _empty_context_json()
        else:
            context = _validate_context_json(context)

        now = datetime.utcnow()
        cv = CV(
            id="",  # el repo asigna
            user_id=user_id,
            title=input.title,
            context_json=context,
            created_at=now,
            updated_at=now,
        )
        saved = self._repo.create(cv)
        return _cv_to_response(saved)


class GetCV:
    def __init__(self, cv_repo: CVRepository) -> None:
        self._repo = cv_repo

    def execute(self, user_id: str, input: GetCVInput) -> CVResponse:
        cv = self._repo.get(input.cv_id, user_id)
        return _cv_to_response(cv)


class ListCVs:
    def __init__(self, cv_repo: CVRepository) -> None:
        self._repo = cv_repo

    def execute(self, user_id: str, input: ListCVsInput) -> Sequence[CVResponse]:
        cvs = self._repo.list_for_user(user_id)
        return [_cv_to_response(cv) for cv in cvs]


class UpdateCV:
    def __init__(self, cv_repo: CVRepository) -> None:
        self._repo = cv_repo

    def execute(self, user_id: str, input: UpdateCVInput) -> CVResponse:
        if input.title is None and input.context_json is None:
            raise ValidationError("body", "Debe enviar al menos title o context_json")

        cv = self._repo.get(input.cv_id, user_id)
        if input.title is not None:
            cv.update_title(input.title)
        if input.context_json is not None:
            normalized = _validate_context_json(input.context_json)
            cv.update_context(normalized)
        updated = self._repo.update(cv)
        return _cv_to_response(updated)


class DeleteCV:
    def __init__(self, cv_repo: CVRepository) -> None:
        self._repo = cv_repo

    def execute(self, user_id: str, input: DeleteCVInput) -> None:
        self._repo.delete(input.cv_id, user_id)


class GetChat:
    def __init__(self, chat_repo: ChatRepository) -> None:
        self._repo = chat_repo

    def execute(self, user_id: str, cv_id: str) -> list[ChatMessage]:
        return self._repo.get_messages(cv_id, user_id)


class AppendChat:
    def __init__(self, chat_repo: ChatRepository) -> None:
        self._repo = chat_repo

    def execute(
        self, user_id: str, cv_id: str, role: str, content: str, patch: dict | None
    ) -> ChatMessage:
        msg = ChatMessage(role=role, content=content, patch=patch)
        self._repo.append(cv_id, user_id, msg)
        return msg


class ClearChat:
    def __init__(self, chat_repo: ChatRepository) -> None:
        self._repo = chat_repo

    def execute(self, user_id: str, cv_id: str) -> None:
        self._repo.clear(cv_id, user_id)
