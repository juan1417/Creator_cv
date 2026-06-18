"""Capa web: Flask routes que adaptan HTTP a use cases.

Esta capa NO contiene lógica de negocio — solo:
1. Parsea el request (path params, query, body, headers)
2. Llama al use case
3. Serializa la respuesta
4. Maneja errores (traduce excepciones de dominio a HTTP)
"""
from .flask_app import create_flask_app
from .routes import register_routes
from .errors import register_error_handlers

__all__ = ["create_flask_app", "register_routes", "register_error_handlers"]
