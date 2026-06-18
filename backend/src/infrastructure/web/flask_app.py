"""Flask app factory: crea la app con sus middlewares.

Se llama desde main.py con la composición de dependencias (DI).
"""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS


def create_flask_app() -> Flask:
    app = Flask(__name__)
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        expose_headers=["Content-Disposition"],
    )
    return app
