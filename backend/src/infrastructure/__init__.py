"""Infrastructure layer: adapters a frameworks externos (Supabase, Flask, etc).

Aquí vive TODO lo que depende de una tecnología específica:
- SupabaseCVRepository: cómo persistir CVs en Supabase
- SupabaseChatRepository: cómo persistir chats en Supabase
- SupabaseAuthVerifier: cómo verificar el JWT de Supabase
- Flask: cómo exponer los use cases como endpoints HTTP
"""
from .persistence.supabase_cv_repo import SupabaseCVRepository
from .persistence.supabase_chat_repo import SupabaseChatRepository
from .auth.supabase_auth import SupabaseAuthVerifier

__all__ = [
    "SupabaseCVRepository",
    "SupabaseChatRepository",
    "SupabaseAuthVerifier",
]
