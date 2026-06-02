"""Gemini integration for CV adaptation and review.

Two-step process:

1. **Adapt**: send the user's CV (as JSON) + the job offer text. Force
   the response to follow :class:`CVSchema` via ``response_json_schema``.
2. **Review**: ask Gemini for 3-5 concrete, actionable suggestions in
   Markdown to improve the candidacy.

Both calls share the same Gemini client and use the configured model
(default ``gemini-2.5-flash``).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from .config import Config
from .schemas import CVSchema, validate_cv

log = logging.getLogger(__name__)


# --- Prompts ---


ADAPT_PROMPT = """Eres un experto en redacción de CVs y selección de personal. \
Adapta el siguiente CV a la oferta de trabajo indicada. \
NO inventes experiencias, títulos, certificaciones ni proyectos. \
Solo puedes:
  1. Reescribir `perfil_profesional.resumen` para destacar lo relevante a la oferta.
  2. Reformular bullets de `experiencia[].responsabilidades` y `logros` con \
verbos de acción y, cuando sea posible, métricas.
  3. Reordenar y filtrar `habilidades.tecnicas`, `habilidades.blandas` e \
`habilidades.idiomas` poniendo primero las que coincidan con la oferta.
  4. Reordenar las `experiencia[]` poniendo arriba las más relevantes.
  5. Mantener el idioma y tono del CV original.

Devuelve EXCLUSIVAMENTE un JSON con el mismo esquema del CV. \
No incluyas texto, markdown ni explicaciones fuera del JSON.

CV ORIGINAL (JSON):
{cv}

OFERTA DE TRABAJO:
{offer}
"""


REVIEW_PROMPT = """Eres un coach de carrera. Dado este CV ya adaptado y la \
oferta objetivo, proporciona entre 3 y 5 sugerencias concretas y \
accionables en Markdown (usando bullets `-`) que el usuario podría aplicar \
para mejorar su candidatura. Enfócate en: gaps visibles entre el CV y la \
oferta, habilidades que debería reforzar, proyectos a destacar mejor, o \
cómo presentar mejor sus logros. Sé conciso (1-2 líneas por sugerencia). \
Empieza directamente con el primer bullet, sin título ni introducción.

CV ADAPTADO (JSON):
{cv}

OFERTA DE TRABAJO:
{offer}
"""


# Iteration feedback: tells Gemini what's missing so the next attempt
# can close the gaps. The prompt is intentionally short and concrete.
ITERATION_FEEDBACK_PROMPT = """Tu adaptación anterior del CV alcanzó un score de {score}/100 \
frente a la oferta de trabajo. NO alcanzó el objetivo de {target}/100.

Skills técnicas faltantes (NO presentes en tu CV adaptado, pero sí requeridas \
por la oferta): {missing_skills}

Idiomas faltantes: {missing_langs}

TAREA PARA ESTE INTENTO:
1. Vuelve a adaptar el CV, esta vez incluyendo las skills técnicas faltantes \
en `experiencia[].responsabilidades` y `logros` (describe proyectos concretos \
donde se usaron, sin inventar empresas).
2. Si el idioma faltante es razonablemente presente en el CV, márcalo en \
`habilidades.idiomas`. Si NO lo está, déjalo fuera (no inventes).
3. Reordena `habilidades.tecnicas` poniendo las que coincidan con la oferta \
al principio.
4. Mantén todo lo demás válido y coherente con el CV original.

Devuelve EXCLUSIVAMENTE un JSON con el mismo esquema. Sin texto extra.

CV ORIGINAL (JSON):
{cv}

OFERTA:
{offer}
"""


# Improve: general-purpose CV upgrade WITHOUT a job offer. The goal is
# to raise the *generic* quality of the CV so it scores better on any
# offer: stronger resumen, action-verb bullets, metrics where plausible,
# better keywords in skills.
IMPROVE_PROMPT = """Eres un experto senior en redacción de CVs profesionales. \
Voy a pasarte el JSON de un CV. Tu objetivo es REFORMULARLO para que sea más \
fuerte y competitivo en general (no está enfocado a una oferta concreta).

Reglas CRÍTICAS:
- NO inventes empresas, títulos, fechas, certificaciones ni proyectos.
- NO inventes métricas específicas con números exactos si no hay base. \
En su lugar, usa formulaciones cualitativas ("redujo latencia \
significativamente", "mejoró el throughput del equipo") o describe \
`logros` cualitativos plausibles coherentes con la responsabilidad.
- Si un campo está vacío, déjalo vacío.

TAREAS:
1. Reescribe `perfil_profesional.resumen` para que sea un párrafo de 2-4 \
líneas potente: empieza con el título profesional + años de experiencia + \
2-3 áreas de especialización. Tono profesional, sin clichés.
2. Convierte cada `experiencia[].responsabilidades` en bullets que \
empiecen con verbos de acción fuertes (Diseñé, Lideré, Implementé, \
Optimizé, Reduje, etc.) y, cuando sea posible, terminen en un \
resultado medible o impacto ("reduciendo X en Y%", "sirviendo a N \
usuarios", "liderando equipo de M personas").
3. Añade/mejora `experiencia[].logros` con 1-2 logros cuantitativos \
o cualitativos por experiencia (solo si hay base real).
4. Reordena y limpia `habilidades.tecnicas`: pon primero las más \
demandadas en el mercado actual (cloud, lenguajes, frameworks, \
herramientas), agrupa implícitamente, y elimina ruido.
5. Mejora `proyectos[].descripcion` para que sea de 1-2 líneas con \
enfoque en impacto, no en features.
6. Reescribe las fortalezas para que sean 3-5 frases de alto impacto \
(evita "buen compañero de equipo" o "trabajador"; prefiere \
"resolución de problemas complejos", "comunicación técnica clara", \
"ownership de proyectos end-to-end").

Devuelve EXCLUSIVAMENTE un JSON con el mismo esquema. Sin texto extra.

CV ORIGINAL (JSON):
{cv}
"""


# --- Public API ---


def is_configured() -> bool:
    return bool(Config.GEMINI_API_KEY)


def _get_client() -> genai.Client:
    if not Config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY no configurada")
    return genai.Client(api_key=Config.GEMINI_API_KEY)


def _call_json(client: genai.Client, prompt: str) -> dict[str, Any]:
    """Single Gemini call that returns parsed JSON matching CVSchema.

    Retries on transient 5xx errors with a short exponential backoff.
    """
    text = _generate_with_retry(
        client,
        prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=CVSchema.model_json_schema(),
            temperature=0.4,
        ),
    )
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini devolvió JSON inválido: {e}") from e


def _call_text(client: genai.Client, prompt: str) -> str:
    text = _generate_with_retry(
        client,
        prompt,
        config=types.GenerateContentConfig(temperature=0.5),
    )
    return (text or "").strip()


def _generate_with_retry(
    client: genai.Client,
    prompt: str,
    config: types.GenerateContentConfig,
    max_retries: int = 3,
) -> str:
    """Call ``generate_content`` and retry on transient errors (503/429).

    Returns ``response.text`` on success; raises on permanent failure.
    """
    import time as _time
    from google.genai import errors as _errors

    delay = 1.5
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=[prompt],
                config=config,
            )
            return response.text or ""
        except _errors.ServerError as e:
            last_exc = e
            status = getattr(e, "code", None) or 0
            if status in (429, 500, 502, 503, 504) and attempt < max_retries:
                log.warning("Gemini %d (attempt %d/%d), retrying in %.1fs", status, attempt + 1, max_retries, delay)
                _time.sleep(delay)
                delay *= 2
                continue
            raise
    # Unreachable, but keeps type-checkers happy.
    if last_exc:
        raise last_exc
    raise RuntimeError("Gemini call failed without exception")


def adapt_cv_to_offer(cv: dict[str, Any], job_offer: str) -> tuple[dict[str, Any], str]:
    """Adapt ``cv`` to ``job_offer`` and return ``(adapted_cv, review_md)``.

    Retries once on validation failure with lower temperature. Raises
    :class:`RuntimeError` if both attempts fail.
    """
    client = _get_client()
    cv_json = json.dumps(cv, ensure_ascii=False, indent=2)

    adapted = _try_adapt(client, cv_json, job_offer)
    review = _call_text(
        client,
        REVIEW_PROMPT.format(cv=json.dumps(adapted, ensure_ascii=False, indent=2), offer=job_offer),
    )
    return adapted, review


def _try_adapt(client: genai.Client, cv_json: str, offer: str) -> dict[str, Any]:
    prompt = ADAPT_PROMPT.format(cv=cv_json, offer=offer)
    raw = _call_json(client, prompt)
    try:
        return validate_cv(raw)
    except ValidationError:
        # retry once with lower temperature
        log.warning("Adapt response failed validation, retrying with temperature=0.2")
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=CVSchema.model_json_schema(),
                temperature=0.2,
            ),
        )
        try:
            return validate_cv(json.loads(response.text or ""))
        except (json.JSONDecodeError, ValidationError) as e:
            raise RuntimeError(f"Gemini no pudo producir un CV válido: {e}") from e


def adapt_until_score(
    cv: dict,
    job_offer: str,
    target_score: int = 70,
    max_iterations: int = 5,
    on_progress=None,
) -> tuple[dict, str, dict]:
    """Iteratively adapt ``cv`` to ``job_offer`` until ``score >= target_score``
    or ``max_iterations`` is reached.

    Returns ``(cv, review_md, loop_meta)`` where ``loop_meta`` is::

        {
            "iterations": <int>,
            "final_score": <int>,
            "target_score": <int>,
            "reached_target": <bool>,
            "scores_per_iteration": [<int>, ...],
        }

    Strategy:
      1. First iteration uses :data:`ADAPT_PROMPT` (no feedback).
      2. Subsequent iterations use :data:`ITERATION_FEEDBACK_PROMPT` with
         the missing skills/langs from the previous attempt.
      3. Track the best-scoring CV across iterations; on exit, return it
         plus a flag indicating whether the target was reached.

    ``on_progress`` is an optional callback ``fn(iteration, score, total)``
    called after each iteration (for UI updates).
    """
    from .match_scorer import score_match

    client = _get_client()
    cv_json = json.dumps(cv, ensure_ascii=False, indent=2)

    # --- Iteration 1: standard adapt ---
    current = _try_adapt(client, cv_json, job_offer)
    score = score_match(current, job_offer)["total"]
    scores = [score]
    best_cv = current
    best_score = score

    if on_progress:
        on_progress(1, score, max_iterations)

    if score >= target_score:
        review = _call_text(
            client,
            REVIEW_PROMPT.format(
                cv=json.dumps(current, ensure_ascii=False, indent=2),
                offer=job_offer,
            ),
        )
        meta = {
            "iterations": 1,
            "final_score": score,
            "target_score": target_score,
            "reached_target": True,
            "scores_per_iteration": scores,
        }
        return current, review, meta

    # --- Iterations 2..N: feedback loop ---
    for it in range(2, max_iterations + 1):
        result = score_match(current, job_offer)
        missing_skills = result["dimensions"]["tecnicas"]["missing"]
        missing_langs = result["dimensions"]["idiomas"]["missing"]

        feedback_prompt = ITERATION_FEEDBACK_PROMPT.format(
            score=score,
            target=target_score,
            missing_skills=", ".join(missing_skills) or "(ninguna)",
            missing_langs=", ".join(missing_langs) or "(ninguno)",
            cv=cv_json,
            offer=job_offer,
        )
        try:
            current = _try_adapt(client, feedback_prompt, job_offer)
        except RuntimeError as e:
            log.warning("Iteration %d adapt failed: %s", it, e)
            break

        score = score_match(current, job_offer)["total"]
        scores.append(score)

        if score > best_score:
            best_score = score
            best_cv = current

        if on_progress:
            on_progress(it, score, max_iterations)

        if score >= target_score:
            break

    review = _call_text(
        client,
        REVIEW_PROMPT.format(
            cv=json.dumps(best_cv, ensure_ascii=False, indent=2),
            offer=job_offer,
        ),
    )
    meta = {
        "iterations": len(scores),
        "final_score": best_score,
        "target_score": target_score,
        "reached_target": best_score >= target_score,
        "scores_per_iteration": scores,
    }
    return best_cv, review, meta


def improve_cv(cv: dict) -> dict:
    """General-purpose CV improvement (no job offer needed).

    Returns a new CV dict with stronger resumen, action-verb bullets,
    qualitative achievements, and reordered skills. Raises
    :class:`RuntimeError` if Gemini is not configured or returns
    invalid data.
    """
    from .schemas import validate_cv

    client = _get_client()
    cv_json = json.dumps(cv, ensure_ascii=False, indent=2)
    prompt = IMPROVE_PROMPT.format(cv=cv_json)
    raw = _call_json(client, prompt)
    return validate_cv(raw)


__all__ = ["is_configured", "adapt_cv_to_offer", "adapt_until_score", "improve_cv"]

# silence unused
_ = os
