"""Flask app factory: crea la app con sus middlewares.

Se llama desde ``composition/app_factory.py`` con la configuración efectiva.
"""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS


def create_flask_app(cors_origins: list[str] | str = "*") -> Flask:
    """Crea la instancia de Flask con CORS configurado para ``/api/*``.

    Args:
        cors_origins: lista de orígenes permitidos (ej. ``["https://app.com"]``)
            o ``"*"`` para cualquiera. Por defecto ``"*"``.
    """
    app = Flask(__name__)
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        expose_headers=["Content-Disposition"],
    )
    return app
