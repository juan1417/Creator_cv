"""Composition root: donde se cablean todas las dependencias.

Aquí es donde se decide QUÉ implementación usar para CADA interfaz.
Es el ÚNICO lugar donde el dominio se conecta con la infrastructure.

Si querés cambiar Supabase por otro DB, solo tocás este archivo.
Si querés cambiar Flask por FastAPI, solo tocás la capa web.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from supabase import Client, create_client

from ..application.use_cases import (
    AppendChat,
    ClearChat,
    CreateCV,
    DeleteCV,
    GetCV,
    GetChat,
    ListCVs,
    UpdateCV,
)
from ..domain.repositories import CVRepository, ChatRepository
from ..infrastructure.auth.supabase_auth import SupabaseAuthVerifier
from ..infrastructure.persistence.supabase_chat_repo import SupabaseChatRepository
from ..infrastructure.persistence.supabase_cv_repo import SupabaseCVRepository
from ..infrastructure.web.errors import register_error_handlers
from ..infrastructure.web.flask_app import create_flask_app
from ..infrastructure.web.routes import register_routes


@dataclass
class AppConfig:
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    cors_origins: str
    is_production: bool

    @classmethod
    def from_env(cls) -> "AppConfig":
        url = os.environ.get("SUPABASE_URL", "").strip()
        # La anon key se usa para el cliente público (no la usamos en backend
        # porque validamos JWT directamente con el service key).
        anon = os.environ.get("SUPABASE_ANON_KEY", "").strip()
        # El service key es la "llave maestra" del backend. Bypasea RLS.
        service = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        if not url or not service:
            raise RuntimeError(
                "Faltan SUPABASE_URL y/o SUPABASE_SERVICE_ROLE_KEY en el entorno. "
                "Configuralas en Railway → Variables antes de deployar."
            )
        return cls(
            supabase_url=url,
            supabase_anon_key=anon,
            supabase_service_key=service,
            cors_origins=os.environ.get("CORS_ORIGINS", "*").strip(),
            is_production=os.environ.get("RAILWAY_ENVIRONMENT") == "production"
            or os.environ.get("FLASK_ENV") == "production",
        )


def build_app():
    """Construye la app Flask con todas las dependencias cableadas."""
    cfg = AppConfig.from_env()
    app = create_flask_app()

    # Cliente Supabase con service_role (bypasea RLS — la auth la hace el verifier)
    supabase: Client = create_client(cfg.supabase_url, cfg.supabase_service_key)

    # Adapters
    cv_repo: CVRepository = SupabaseCVRepository(supabase)
    chat_repo: ChatRepository = SupabaseChatRepository(supabase)
    auth_verifier = SupabaseAuthVerifier(supabase)

    # Use cases
    register_routes(
        app,
        create_cv=CreateCV(cv_repo),
        get_cv=GetCV(cv_repo),
        list_cvs=ListCVs(cv_repo),
        update_cv=UpdateCV(cv_repo),
        delete_cv=DeleteCV(cv_repo),
        get_chat=GetChat(chat_repo),
        append_chat=AppendChat(chat_repo),
        clear_chat=ClearChat(chat_repo),
        auth_verifier=auth_verifier,
    )

    register_error_handlers(app)
    return app
