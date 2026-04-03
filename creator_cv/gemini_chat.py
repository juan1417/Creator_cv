"""Entrevista asistida por Gemini (chat en la web; misma API que el MCP gemini_server)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai
from google.genai import types

CAPACITY_INSTRUCTIONS: dict[str, str] = {
    "principiante": (
        "Capacidad del usuario: principiante en redacción de CV o poco tiempo. "
        "Usa frases muy cortas, una pregunta clara por turno (como máximo dos), "
        "vocabulario simple y un mini-ejemplo cuando ayude. No asumas jerga. "
        "Si la persona no sabe algo, dile que puede dejarlo en blanco o en dudas."
    ),
    "intermedio": (
        "Capacidad del usuario: intermedio. "
        "Hasta dos o tres preguntas por turno cuando encajen. "
        "Pide logros concretos cuando sea natural, sin presionar."
    ),
    "avanzado": (
        "Capacidad del usuario: avanzado. "
        "Puedes pedir impacto en métricas, alcance técnico y contexto de negocio. "
        "Sé directo y evita relleno."
    ),
}


def _client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "Falta GEMINI_API_KEY en el entorno (.env en la raíz del proyecto)."
        )
    return genai.Client(api_key=key)


def _model_id() -> str:
    return (os.environ.get("GEMINI_MODEL") or "gemini-2.0-flash").strip()


def summarize_cv_for_prompt(data: dict[str, Any], max_chars: int = 7000) -> str:
    try:
        s = json.dumps(data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        s = str(data)
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 40] + "\n… [contexto truncado para el modelo]"


def build_system_instruction(capacity_key: str, cv_json_text: str) -> str:
    cap = CAPACITY_INSTRUCTIONS.get(
        capacity_key,
        CAPACITY_INSTRUCTIONS["intermedio"],
    )
    return f"""Eres un entrevistador profesional para armar un currículum en español (puedes seguir el idioma del usuario si escribe en otro).

{cap}

Reglas estrictas:
- No inventes fechas, empresas, títulos, certificaciones ni cifras. Solo usa lo que la persona diga o lo que ya figure en el contexto JSON.
- Si falta un dato, pregunta o sugiere dejarlo en "dudas_pendientes" en el bloque técnico.
- Mantén tono profesional y empático.

Contexto JSON actual del CV (fuente de verdad; puedes proponer actualizaciones solo si la conversación aporta datos nuevos explícitos):
```json
{cv_json_text}
```

Formato de salida:
1) Responde en lenguaje natural al usuario (preguntas y comentarios).
2) SOLO si la persona confirmó datos nuevos o rellenó campos que deben guardarse en el CV, añade al FINAL un bloque exactamente así (si no hay nada nuevo confirmado, NO incluyas el bloque):
```cv-context
{{ ... objeto JSON parcial con las claves de nivel superior a fusionar (mismo esquema que el contexto: meta, perfil_profesional, experiencia, educacion, habilidades, proyectos, etc.) ... }}
```

En el bloque cv-context: objetos anidados se fusionan con lo existente; listas como "experiencia" reemplazan solo si incluyes la lista completa que la persona validó en este turno — si no estás seguro, omite el bloque y sigue preguntando.
"""


def extract_cv_context_block(assistant_text: str) -> tuple[str, dict[str, Any] | None]:
    """
    Devuelve (texto sin el bloque cv-context para mostrar, parche dict o None).
    """
    pattern = re.compile(r"```cv-context\s*([\s\S]*?)```", re.IGNORECASE)
    m = pattern.search(assistant_text)
    if not m:
        return assistant_text.strip(), None
    raw = m.group(1).strip()
    try:
        patch = json.loads(raw)
    except json.JSONDecodeError:
        return assistant_text.strip(), None
    if not isinstance(patch, dict):
        return assistant_text.strip(), None
    visible = (assistant_text[: m.start()] + assistant_text[m.end() :]).strip()
    return visible, patch


def run_chat_turn(
    *,
    history: list[dict[str, str]],
    user_message: str,
    capacity_key: str,
    cv_data: dict[str, Any],
) -> tuple[str, dict[str, Any] | None]:
    """
    history: [{"role":"user"|"assistant","content":"..."}]
    Retorna texto visible del asistente (sin bloque técnico en UI) y parche opcional.
    """
    client = _client()
    system = build_system_instruction(
        capacity_key,
        summarize_cv_for_prompt(cv_data),
    )
    transcript_parts: list[str] = []
    for turn in history[-24:]:
        role = turn.get("role", "")
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        label = "Usuario" if role == "user" else "Asistente"
        transcript_parts.append(f"{label}:\n{content}")
    transcript_parts.append(f"Usuario:\n{user_message.strip()}")
    prompt = "\n\n--- Turno siguiente ---\n\n".join(transcript_parts)

    cfg = types.GenerateContentConfig(
        system_instruction=system,
        temperature=0.55,
    )
    resp = client.models.generate_content(
        model=_model_id(),
        contents=prompt,
        config=cfg,
    )
    raw_text = getattr(resp, "text", None) or ""
    if not raw_text.strip() and resp.candidates:
        chunks: list[str] = []
        for c in resp.candidates:
            if c.content and c.content.parts:
                for p in c.content.parts:
                    if getattr(p, "text", None):
                        chunks.append(p.text)
        raw_text = "\n".join(chunks)

    visible, patch = extract_cv_context_block(raw_text)
    if not visible and patch is not None:
        visible = "He preparado una actualización del contexto. Revisa y aplica si coincide con lo que dijiste."
    elif not visible:
        visible = raw_text.strip() or "(Sin respuesta del modelo.)"
    return visible, patch
