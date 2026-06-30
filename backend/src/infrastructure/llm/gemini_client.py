"""Google Gemini LLM client for CV analysis."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

ATS_SYSTEM_PROMPT = """Sos un experto en optimización de CVs para sistemas ATS (Applicant Tracking Systems).
Tu objetivo es ayudar al usuario a pasar los filtros automáticos que usan las empresas para pre-candidatos.

## Reglas ATS que siempre debés aplicar:

### Formato
- Palabras clave exactas del sector deben aparecer en el CV (no sinónimos)
- Formato simple: sin tablas, sin columnas complejas, sin imágenes, sin emojis
- Fechas en formato consistente (mes. año o mm/yyyy)
- Títulos de sección estándar: Experiencia, Educación, Habilidades, Proyectos
- Evitar abreviaturas no estándar (escribir "JavaScript" no "JS")
- Sin encabezados ni pies de página complejos

### Contenido
- Verbos de acción al inicio de cada bullet point (Desarrollé, Implementé, Lideré)
- Cuantificar logros con números siempre que sea posible ("Reduje el tiempo de carga un 40%")
- Skills técnicas como lista de palabras clave exactas (no oraciones)
- Perfil profesional: 2-3 líneas máximo, con keywords de la industria
- Experiencia: orden cronológico inverso, con métricas

### Palabras clave
- Detectar keywords faltantes comparando con la industria/rol del usuario
- Sugerir agregar keywords que los ATS buscan pero que no están en el CV
- No recomendar keywords que no sean relevantes para el rol

## Cómo responder:
- Sé directo y accionable. Sin rodeos.
- Si el usuario pide un cambio concreto (ej: "reescribí mi resumen"), hacelo y mostrá el resultado
- Si sugieris un cambio que modifica el CV, devolvé un "patch" JSON para que el frontend lo pueda aplicar
- El patch debe tener esta estructura:
  {"section": "experiencia|educacion|habilidades|proyectos|perfil_profesional|meta", "action": "update|add|remove", "index": <número si aplica>, "field": "campo", "value": "nuevo valor"}
- Podés devolver múltiples patches en un array

## Formato de respuesta:
- Respondé en español
- Usá markdown ligero (**negrita**, listas) para legibilidad
- Si devolvés un patch, ponlo en un bloque ```json al final de tu respuesta"""


@dataclass
class ComparisonResult:
    score: int
    verdict: str
    sub_scores: dict[str, int]
    improvements: list[dict[str, str]]
    strengths: list[str]
    gaps: list[str]


@dataclass
class ChatResult:
    response: str
    patches: list[dict] = field(default_factory=list)


class GeminiClient:
    def __init__(self, api_key: str) -> None:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash")
        self._ats_model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=ATS_SYSTEM_PROMPT,
        )

    def compare_cv_vs_offer(
        self, cv_text: str, job_title: str, job_description: str
    ) -> ComparisonResult:
        prompt = f"""Analiza este CV contra esta oferta laboral y devuelve un JSON.

CV:
{cv_text}

Oferta laboral - Puesto: {job_title}
Descripción:
{job_description}

Responde EXCLUSIVAMENTE con JSON válido (sin markdown, sin ```), con esta estructura exacta:
{{
  "score": <número 0-100>,
  "verdict": "<excelente|bueno|regular|bajo>",
  "sub_scores": {{
    "experiencia": <0-100>,
    "habilidades": <0-100>,
    "educacion": <0-100>,
    "formato": <0-100>
  }},
  "improvements": [
    {{"title": "título corto", "description": "descripción de la mejora", "priority": "alta|media|baja"}}
  ],
  "strengths": ["fortaleza 1", "fortaleza 2"],
  "gaps": ["falta 1", "falta 2"]
}}

Reglas:
- score debe reflejar qué tan bien el CV se alinea con la oferta
- sub_scores: experiencia (años/relevancia), habilidades (match técnico), educacion (formación), formato (estructura/ATS)
- improvements: máx 6 sugerencias concretas y accionables
- strengths: 2-4 fortalezas del CV para esta oferta
- gaps: 2-4 áreas donde el CV no cubre la oferta
- verdict: excelente (80+), bueno (60-79), regular (40-59), bajo (<40)
"""

        try:
            response = self._model.generate_content(prompt)
            raw_text = response.text.strip()
            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            data = json.loads(raw_text)

            return ComparisonResult(
                score=int(data.get("score", 0)),
                verdict=str(data.get("verdict", "regular")),
                sub_scores={
                    "experiencia": int(data.get("sub_scores", {}).get("experiencia", 0)),
                    "habilidades": int(data.get("sub_scores", {}).get("habilidades", 0)),
                    "educacion": int(data.get("sub_scores", {}).get("educacion", 0)),
                    "formato": int(data.get("sub_scores", {}).get("formato", 0)),
                },
                improvements=[
                    {
                        "title": str(imp.get("title", "")),
                        "description": str(imp.get("description", "")),
                        "priority": str(imp.get("priority", "media")),
                    }
                    for imp in data.get("improvements", [])
                ],
                strengths=[str(s) for s in data.get("strengths", [])],
                gaps=[str(g) for g in data.get("gaps", [])],
            )
        except Exception:
            log.exception("Gemini comparison failed")
            # Return a fallback result
            return ComparisonResult(
                score=0,
                verdict="error",
                sub_scores={"experiencia": 0, "habilidades": 0, "educacion": 0, "formato": 0},
                improvements=[],
                strengths=[],
                gaps=["No se pudo analizar el CV. Verificá la configuración de la API key."],
            )

    def chat(
        self, message: str, cv_text: str, history: list[dict[str, str]] | None = None
    ) -> ChatResult:
        """Send a message to the ATS-optimized chat model with CV context."""
        try:
            chat = self._ats_model.start_chat(history=history or [])

            prompt = f"""CV actual del usuario:
```json
{cv_text}
```

Mensaje del usuario: {message}"""

            response = chat.send_message(prompt)
            raw_text = response.text.strip()

            # Extract patch if present (in ```json block at the end)
            patches = []
            if "```json" in raw_text:
                parts = raw_text.split("```json")
                if len(parts) > 1:
                    patch_block = parts[-1].split("```")[0].strip()
                    try:
                        parsed = json.loads(patch_block)
                        if isinstance(parsed, list):
                            patches = parsed
                        elif isinstance(parsed, dict):
                            patches = [parsed]
                    except json.JSONDecodeError:
                        pass
                    # Remove the json block from the response text
                    raw_text = raw_text.split("```json")[0].strip()

            return ChatResult(response=raw_text, patches=patches)

        except Exception:
            log.exception("Gemini chat failed")
            return ChatResult(
                response="No pude procesar tu solicitud. Verificá que la API key de Gemini esté configurada correctamente.",
                patches=[],
            )
