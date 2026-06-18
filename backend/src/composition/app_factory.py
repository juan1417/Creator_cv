from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

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
from ..domain.repositories import ChatRepository, CVRepository
from ..infrastructure.auth.local_auth import verify_token
from ..infrastructure.persistence.database import create_all, get_session
from ..infrastructure.persistence.sqlalchemy_chat_repo import SQLAlchemyChatRepository
from ..infrastructure.persistence.sqlalchemy_cv_repo import SQLAlchemyCVRepository
from ..infrastructure.web.errors import register_error_handlers
from ..infrastructure.web.flask_app import create_flask_app
from ..infrastructure.web.routes import register_routes


@dataclass
class AppConfig:
    cors_origins: str
    is_production: bool
    database_url: str 
    secret_key: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            cors_origins=os.environ.get("CORS_ORIGINS", "*").strip(),
            is_production=os.environ.get("RAILWAY_ENVIRONMENT") == "production"
            or os.environ.get("FLASK_ENV") == "production",
            database_url=os.environ.get("DATABASE_URL", "").strip(),
            secret_key=os.environ.get("JWT_SECRET_KEY")
            or os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod"),
        )


def build_app():
    cfg = AppConfig.from_env()
    app = create_flask_app()
    app.config["SECRET_KEY"] = cfg.secret_key

    create_all()

    cv_repo: CVRepository = SQLAlchemyCVRepository()
    chat_repo: ChatRepository = SQLAlchemyChatRepository()

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
        auth_verifier=verify_token,
        get_session_factory=get_session,
    )

    register_error_handlers(app)
    return app
