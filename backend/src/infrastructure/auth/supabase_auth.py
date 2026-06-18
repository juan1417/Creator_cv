"""Verifica el JWT de Supabase y extrae el user_id.

El frontend envía el access_token de Supabase en:
    Authorization: Bearer <token>

Verificamos con la API de Supabase (getUser) y devolvemos el user_id.
"""
from __future__ import annotations

from supabase import Client

from ...domain.exceptions import UnauthorizedError


class SupabaseAuthVerifier:
    def __init__(self, client: Client) -> None:
        self._client = client

    def verify(self, bearer_token: str) -> str:
        """Devuelve el user_id (UUID) o lanza UnauthorizedError."""
        if not bearer_token or not bearer_token.strip():
            raise UnauthorizedError("Falta el token de autenticación")
        token = bearer_token.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        try:
            response = self._client.auth.get_user(token)
        except Exception as e:
            raise UnauthorizedError(f"Token inválido: {e}") from e
        user = getattr(response, "user", None)
        if not user or not getattr(user, "id", None):
            raise UnauthorizedError("Token sin usuario asociado")
        return user.id
