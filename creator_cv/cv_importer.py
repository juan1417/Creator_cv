"""Import an existing CV (PDF or DOCX) into the app.

Two stages:

1. **extract_text(file_storage)** — read the bytes and pull out the
   plain text. Supports ``.pdf`` (pypdf) and ``.docx`` (python-docx).
2. **parse_cv_text(text)** — call Gemini to convert the free-form text
   into a JSON dict matching :class:`CVSchema`. Falls back to a minimal
   raw dump if Gemini is not configured.

Both stages are independent so they can be tested and reused.
"""

from __future__ import annotations

import io
import logging
import os
from typing import Any

from pydantic import ValidationError

from .config import Config
from .schemas import CVSchema, validate_cv

log = logging.getLogger(__name__)


# Max file size: 10 MB
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


# --- Stage 1: text extraction ---


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in {
        ext.lstrip(".") for ext in ALLOWED_EXTENSIONS
    }


def extract_text(file_storage: Any) -> str:
    """Extract plain text from a ``werkzeug.FileStorage`` (or any object
    exposing ``.filename`` and ``.read()``).

    Raises :class:`ValueError` on unsupported type or empty content.
    """
    filename = (getattr(file_storage, "filename", "") or "").lower()
    if not allowed_file(filename):
        raise ValueError(
            f"Tipo de archivo no soportado: {filename}. Usa PDF o DOCX."
        )

    raw = file_storage.read()
    if not raw:
        raise ValueError("El archivo está vacío.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"Archivo demasiado grande ({len(raw) // 1024} KB). Máximo 10 MB."
        )

    if filename.endswith(".pdf"):
        return _extract_pdf(raw)
    if filename.endswith(".docx"):
        return _extract_docx(raw)
    raise ValueError(f"Extensión desconocida: {filename}")


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    chunks: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as e:  # pragma: no cover - depends on PDF
            log.warning("PDF page %d extraction failed: %s", i, e)
            text = ""
        if text.strip():
            chunks.append(text)
    full = "\n".join(chunks).strip()
    if not full:
        raise ValueError(
            "No se pudo extraer texto del PDF. "
            "Si está escaneado (imagen), necesitas un CV digital."
        )
    return full


def _extract_docx(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    parts: list[str] = []
    # Iterate paragraphs in document order, including those inside tables.
    for block in doc.iter_inner_content():
        if hasattr(block, "text"):
            text = (block.text or "").strip()
            if text:
                parts.append(text)
        elif hasattr(block, "rows"):  # Table
            for row in block.rows:
                cells = [c.text.strip() for c in row.cells if c.text and c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
    full = "\n".join(parts).strip()
    if not full:
        raise ValueError("El DOCX no contiene texto extraíble.")
    return full


# --- Stage 2: Gemini parsing (text → CVSchema) ---


PARSE_PROMPT = """Eres un experto en extracción de datos de CVs. A continuación te paso \
el texto plano de un currículum vitae. Extrae toda la información y devuélvela \
EXCLUSIVAMENTE como JSON que cumpla este esquema:

- meta.nombre_completo (string)
- meta.titulo_profesional (string o null)
- meta.contacto.email, .telefono, .linkedin, .ubicacion (strings o null)
- perfil_profesional.resumen (string)
- perfil_profesional.palabras_clave (lista de strings)
- experiencia: lista de objetos con empresa, cargo, ubicacion, fecha_inicio, \
fecha_fin, actual (bool), responsabilidades (lista de strings), logros (lista de strings)
- educacion: lista de objetos con institucion, titulo, ubicacion, fecha_inicio, \
fecha_fin, estado
- habilidades.tecnicas, .blandas, .idiomas (listas de strings)
- proyectos: lista de objetos con nombre, descripcion, tecnologias, enlace
- certificaciones (lista de strings)
- fortalezas (lista de strings)

Reglas:
- NO inventes datos. Si un campo no aparece, déjalo vacío o como lista vacía.
- Conserva tildes, eñes y mayúsculas/minúsculas originales.
- Si un bullet está pegado, sepáralo en items distintos.
- Devuelve SOLO el JSON, sin texto adicional ni markdown.

TEXTO DEL CV:
\"\"\"
{text}
\"\"\"
"""


def _call_parse(client: Any, text: str) -> dict[str, Any]:
    """Single Gemini call: returns parsed JSON matching CVSchema."""
    from google.genai import types

    response = client.models.generate_content(
        model=Config.GEMINI_MODEL,
        contents=[PARSE_PROMPT.format(text=text)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=CVSchema.model_json_schema(),
            temperature=0.2,
        ),
    )
    import json

    return json.loads(response.text or "{}")


def parse_cv_text(text: str) -> dict[str, Any]:
    """Use Gemini to turn free-form CV text into a :class:`CVSchema` dict.

    Raises :class:`RuntimeError` if Gemini is not configured or returns
    invalid data after one retry.
    """
    from .gemini_adapter import _get_client

    client = _get_client()
    try:
        raw = _call_parse(client, text)
        return validate_cv(raw)
    except (ValidationError, ValueError):
        log.warning("Parse response failed validation, retrying with temperature=0.0")
        from google.genai import types
        import json

        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=[PARSE_PROMPT.format(text=text)],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=CVSchema.model_json_schema(),
                temperature=0.0,
            ),
        )
        try:
            return validate_cv(json.loads(response.text or "{}"))
        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"No se pudo parsear el CV con la IA: {e}"
            ) from e


# --- Convenience ---


def import_file_to_cv(file_storage: Any) -> dict[str, Any]:
    """Full pipeline: extract text from the file, parse with Gemini.

    Returns a CV dict ready to be saved.
    """
    text = extract_text(file_storage)
    return parse_cv_text(text)


__all__ = [
    "ALLOWED_EXTENSIONS",
    "MAX_UPLOAD_BYTES",
    "allowed_file",
    "extract_text",
    "parse_cv_text",
    "import_file_to_cv",
]

# silence unused
_ = os
