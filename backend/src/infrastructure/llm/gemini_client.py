"""Google Gemini LLM client for CV analysis."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    score: int
    verdict: str
    sub_scores: dict[str, int]
    improvements: list[dict[str, str]]
    strengths: list[str]
    gaps: list[str]


class GeminiClient:
    def __init__(self, api_key: str) -> None:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash")

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
