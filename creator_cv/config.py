"""Application configuration.

Loads settings from environment variables via python-dotenv. Keep
secrets out of version control — copy .env.example to .env and edit.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Carga .env desde la raíz del proyecto (un nivel arriba de este paquete).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Config:
    """Base configuration shared by all environments."""

    # --- Flask core ---
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    # --- Database ---
    # SQLAlchemy accepts ``sqlite:///C:/path/to/db.sqlite3`` (three slashes
    # followed by a Windows drive letter) — no need for four slashes on
    # Windows. We just pass the absolute posix path.
    _DEFAULT_DB_PATH = (_PROJECT_ROOT / "instance" / "creator_cv.sqlite3").as_posix()
    _DEFAULT_DB_URI = f"sqlite:///{_DEFAULT_DB_PATH}"
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", _DEFAULT_DB_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # --- CSRF (Flask-WTF) ---
    WTF_CSRF_TIME_LIMIT: int | None = None  # tokens válidos por la sesión

    # --- Gemini (opcional) ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- UI ---
    APP_NAME: str = "Creator CV"

    @classmethod
    def gemini_configured(cls) -> bool:
        return bool(cls.GEMINI_API_KEY)


class DevConfig(Config):
    DEBUG: bool = os.getenv("FLASK_DEBUG", "1") == "1"


class ProdConfig(Config):
    DEBUG: bool = False


def get_config() -> type[Config]:
    env = os.getenv("FLASK_ENV", "development").lower()
    if env in {"production", "prod"}:
        return ProdConfig
    return DevConfig
