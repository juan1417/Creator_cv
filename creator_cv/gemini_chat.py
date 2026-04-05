"""Entrevista asistida por Gemini (chat en la web; misma API que el MCP gemini_server)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai
from google.genai import errors as genai_errors
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


def _model_candidates() -> list[str]:
    """Orden: modelo principal + GEMINI_MODEL_FALLBACKS (para 429 por cuota en un modelo)."""
    primary = _model_id()
    raw = os.environ.get(
        "GEMINI_MODEL_FALLBACKS",
        "gemini-2.5-flash,gemini-1.5-flash",
    )
    out: list[str] = [primary]
    for part in raw.split(","):
        p = part.strip()
        if p and p not in out:
            out.append(p)
    return out


def friendly_api_error(exc: Exception) -> str:
    """Mensaje corto para mostrar en la web (sin volcar el JSON completo de Google)."""
    if isinstance(exc, genai_errors.ClientError):
        code = getattr(exc, "code", None)
        msg = (getattr(exc, "message", None) or str(exc))[:500]
        if code == 429:
            return (
                "Cuota o límite de velocidad de Gemini (429). Suele deberse al plan gratuito "
                "agotado para ese modelo o a demasiadas peticiones seguidas. "
                "Prueba: esperar 1–2 minutos; en .env cambia GEMINI_MODEL "
                "(p. ej. gemini-2.5-flash o gemini-1.5-flash); revisa "
                "https://ai.google.dev/gemini-api/docs/rate-limits y el uso en Google AI Studio."
            )
        if code in (401, 403):
            return (
                "La clave GEMINI_API_KEY no es válida o no tiene permiso (401/403). "
                "Genera una nueva en https://aistudio.google.com/apikey"
            )
        if code == 404:
            return (
                f"Modelo no disponible con tu clave o nombre incorrecto: {msg}. "
                "Ajusta GEMINI_MODEL en .env."
            )
        return f"Error de la API Gemini ({code}): {msg}"
    return f"Error del modelo: {exc}"


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
    candidates = _model_candidates()
    resp = None
    last_err: Exception | None = None
    for mid in candidates:
        try:
            resp = client.models.generate_content(
                model=mid,
                contents=prompt,
                config=cfg,
            )
            break
        except genai_errors.APIError as e:
            last_err = e
            code = getattr(e, "code", 0)
            if code == 429 and mid != candidates[-1]:
                continue
            raise RuntimeError(friendly_api_error(e)) from e
    if resp is None:
        raise RuntimeError(
            friendly_api_error(last_err) if last_err else "Sin respuesta del modelo."
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


JOB_FIT_MAX_JOB_CHARS = 24_000
JOB_FIT_MIN_JOB_CHARS = 40

_JOB_FIT_SYSTEM = """Eres un analista de alineación entre un currículum (contexto JSON) y el texto de una oferta de empleo.

Reglas estrictas:
- Basa el análisis SOLO en el JSON del CV y en el texto de la oferta. No inventes experiencias, empresas, títulos, certificaciones, fechas ni métricas.
- Si la oferta exige algo y no hay evidencia clara en el CV, dilo explícitamente (p. ej. «no consta en tu CV» o «no hay evidencia en el contexto»).
- Las valoraciones numéricas o de «encaje» son orientativas y subjetivas; indica que no sustituyen una decisión de selección real.
- Tono profesional y directo. Responde en español (salvo que la oferta esté solo en otro idioma y convenga citar términos en el idioma original entre comillas).

Salida obligatoria en Markdown con estas secciones (en este orden), usando `##` para cada título:
## Resumen del encaje
Un párrafo corto + una línea con **Encaje orientativo (0–10):** X/10 y por qué.

## Requisitos de la oferta vs tu CV
Lista o tabla: requisito o criterio | estado (cubierto / parcial / no consta) | qué dice tu CV (cita breve) | qué falta o es incierto

## Fortalezas para este puesto
Viñetas basadas en datos del CV.

## Brechas y riesgos
Viñetas honestas (incluye «no consta» cuando aplique).

## Cómo mejorar (accionable)
Pasos concretos para el CV o la preparación; no inventes logros: si hace falta información, dilo y sugiere qué añadir o aclarar en el CV.
"""


def run_job_fit_analysis(
    *,
    cv_data: dict[str, Any],
    job_text: str,
) -> str:
    """
    Compara el texto de una oferta con el contexto del CV. Devuelve Markdown (sin HTML).
    """
    job = job_text.strip()
    if len(job) < JOB_FIT_MIN_JOB_CHARS:
        raise ValueError(
            f"Pega un texto de oferta más largo (mínimo ~{JOB_FIT_MIN_JOB_CHARS} caracteres)."
        )
    if len(job) > JOB_FIT_MAX_JOB_CHARS:
        raise ValueError(
            f"El texto es demasiado largo (máximo {JOB_FIT_MAX_JOB_CHARS} caracteres)."
        )

    client = _client()
    cv_json_text = summarize_cv_for_prompt(cv_data, max_chars=8000)
    user_prompt = (
        "Analiza el encaje entre mi CV (JSON) y esta oferta.\n\n"
        "## Contexto JSON del CV\n"
        f"```json\n{cv_json_text}\n```\n\n"
        "## Texto de la oferta\n"
        f"{job}\n"
    )

    cfg = types.GenerateContentConfig(
        system_instruction=_JOB_FIT_SYSTEM.strip(),
        temperature=0.35,
    )
    candidates = _model_candidates()
    resp = None
    last_err: Exception | None = None
    for mid in candidates:
        try:
            resp = client.models.generate_content(
                model=mid,
                contents=user_prompt,
                config=cfg,
            )
            break
        except genai_errors.APIError as e:
            last_err = e
            code = getattr(e, "code", 0)
            if code == 429 and mid != candidates[-1]:
                continue
            raise RuntimeError(friendly_api_error(e)) from e
    if resp is None:
        raise RuntimeError(
            friendly_api_error(last_err) if last_err else "Sin respuesta del modelo."
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
    out = raw_text.strip()
    if not out:
        raise RuntimeError("El modelo devolvió una respuesta vacía.")
    return out
