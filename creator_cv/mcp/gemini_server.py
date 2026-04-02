"""
Servidor MCP (stdio) que expone generación de texto con Google Gemini.
Requiere GEMINI_API_KEY (p. ej. desde la env del cliente MCP en Cursor).

Uso: uv run --group mcp python -m creator_cv.mcp.gemini_server
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / ".env")
from google import genai
from google.genai import types

mcp = FastMCP("creator-cv-gemini")


def _client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "Falta GEMINI_API_KEY: define GEMINI_API_KEY en .env (raíz del repo) "
            "o en la configuración MCP de Cursor."
        )
    return genai.Client(api_key=key)


@mcp.tool()
def gemini_generate(
    prompt: str,
    system_instruction: str = "",
    model: str | None = None,
) -> str:
    """
    Genera una respuesta con Gemini. Usa solo para acelerar borradores;
    el contenido del CV debe seguir siendo el que aporta la persona.
    """
    client = _client()
    mid = (model or os.environ.get("GEMINI_MODEL") or "gemini-2.0-flash").strip()
    cfg = None
    if system_instruction.strip():
        cfg = types.GenerateContentConfig(system_instruction=system_instruction.strip())
    resp = client.models.generate_content(
        model=mid,
        contents=prompt,
        config=cfg,
    )
    text = getattr(resp, "text", None)
    if text:
        return text
    if resp.candidates:
        parts = []
        for c in resp.candidates:
            if c.content and c.content.parts:
                for p in c.content.parts:
                    if getattr(p, "text", None):
                        parts.append(p.text)
        if parts:
            return "\n".join(parts)
    return str(resp)


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
