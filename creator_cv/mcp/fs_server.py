"""
Servidor MCP (stdio) con acceso solo lectura/escritura bajo un directorio raíz.
Uso: uv run --group mcp python -m creator_cv.mcp.fs_server /ruta/absoluta/al/contexto
Reemplaza al `@modelcontextprotocol/server-filesystem` de Node.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastmcp import FastMCP

_ROOT: Path | None = None
mcp = FastMCP("creator-cv-context")


def _root() -> Path:
    if _ROOT is None:
        raise RuntimeError("Raíz MCP no inicializada")
    return _ROOT


def _resolve_under_root(relative_path: str) -> Path:
    if not relative_path or relative_path.startswith(("/", "\\")):
        raise ValueError("Usa rutas relativas al directorio permitido (sin / inicial).")
    norm = relative_path.replace("\\", "/").lstrip("/")
    if ".." in Path(norm).parts:
        raise ValueError("Ruta no permitida (no uses ..).")
    root = _root()
    candidate = (root / norm).resolve()
    candidate.relative_to(root)
    return candidate


@mcp.tool()
def read_text_file(relative_path: str) -> str:
    """Lee un archivo de texto UTF-8 bajo el directorio permitido."""
    path = _resolve_under_root(relative_path.replace("\\", "/").lstrip("/"))
    if not path.is_file():
        raise FileNotFoundError(f"No es un archivo: {relative_path}")
    return path.read_text(encoding="utf-8")


@mcp.tool()
def write_text_file(relative_path: str, content: str) -> str:
    """Escribe contenido UTF-8; crea directorios padre si hace falta."""
    path = _resolve_under_root(relative_path.replace("\\", "/").lstrip("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"OK: escrito {relative_path} ({len(content)} caracteres)"


@mcp.tool()
def list_directory(relative_path: str = "") -> str:
    """Lista nombres en un subdirectorio (vacío = raíz permitida)."""
    rel = (relative_path or ".").replace("\\", "/").lstrip("/")
    path = _resolve_under_root(rel) if rel != "." else _root()
    if not path.is_dir():
        raise NotADirectoryError(f"No es directorio: {relative_path!r}")
    names = sorted(p.name for p in path.iterdir())
    return "\n".join(names) if names else "(vacío)"


def main() -> None:
    global _ROOT
    if len(sys.argv) < 2:
        print(
            "Uso: uv run --group mcp python -m creator_cv.mcp.fs_server <ruta_absoluta_contexto>",
            file=sys.stderr,
        )
        sys.exit(2)
    _ROOT = Path(sys.argv[1]).expanduser().resolve()
    if not _ROOT.is_dir():
        print(f"No existe el directorio: {_ROOT}", file=sys.stderr)
        sys.exit(2)
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
