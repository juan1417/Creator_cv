"""Compare use case: CV vs Job Offer analysis via Gemini."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from ..infrastructure.llm.gemini_client import ComparisonResult, GeminiClient

log = logging.getLogger(__name__)


def _context_to_text(context_json: str) -> str:
    """Convert context_json to readable text for the LLM."""
    try:
        data = json.loads(context_json)
    except (json.JSONDecodeError, TypeError):
        return ""

    lines: list[str] = []
    meta = data.get("meta", {})
    if meta.get("nombre_completo"):
        lines.append(f"Nombre: {meta['nombre_completo']}")
    if meta.get("titulo_profesional"):
        lines.append(f"Título profesional: {meta['titulo_profesional']}")
    if meta.get("objetivo_cv"):
        lines.append(f"Objetivo: {meta['objetivo_cv']}")
    contacto = meta.get("contacto", {})
    if contacto.get("ubicacion"):
        lines.append(f"Ubicación: {contacto['ubicacion']}")

    perfil = data.get("perfil_profesional", {})
    if perfil.get("resumen"):
        lines.append(f"\nResumen profesional: {perfil['resumen']}")

    for exp in data.get("experiencia", []):
        lines.append(
            f"\nExperiencia: {exp.get('puesto', '')} en {exp.get('empresa', '')} "
            f"({exp.get('fecha_inicio', '')} - {exp.get('fecha_fin', '')})"
        )
        for r in exp.get("responsabilidades", []):
            if r:
                lines.append(f"  - {r}")

    for edu in data.get("educacion", []):
        lines.append(
            f"\nEducación: {edu.get('titulo', '')} - {edu.get('institucion', '')} "
            f"({edu.get('fecha_fin', '')})"
        )

    hab = data.get("habilidades", {})
    for key, label in [("tecnicas", "Técnicas"), ("blandas", "Blandas"), ("idiomas", "Idiomas"), ("tecnologias", "Tecnologías")]:
        vals = hab.get(key, [])
        if vals:
            lines.append(f"{label}: {', '.join(vals)}")

    for cert in data.get("certificaciones", []):
        lines.append(f"Certificación: {cert.get('nombre', '')} - {cert.get('institucion', '')}")

    for proj in data.get("proyectos", []):
        lines.append(f"Proyecto: {proj.get('nombre', '')} ({proj.get('rol', '')}) - {proj.get('descripcion', '')}")

    return "\n".join(lines)


@dataclass
class CompareOutput:
    score: int
    verdict: str
    sub_scores: dict[str, int]
    improvements: list[dict[str, str]]
    strengths: list[str]
    gaps: list[str]


class CompareCVWithOffer:
    def __init__(self, gemini_client: GeminiClient) -> None:
        self._client = gemini_client

    def execute(
        self, context_json: str, job_title: str, job_description: str
    ) -> CompareOutput:
        cv_text = _context_to_text(context_json)
        if not cv_text.strip():
            return CompareOutput(
                score=0,
                verdict="bajo",
                sub_scores={"experiencia": 0, "habilidades": 0, "educacion": 0, "formato": 0},
                improvements=[],
                strengths=[],
                gaps=["El CV está vacío. Completá tu perfil antes de comparar."],
            )

        result: ComparisonResult = self._client.compare_cv_vs_offer(
            cv_text, job_title, job_description
        )

        return CompareOutput(
            score=result.score,
            verdict=result.verdict,
            sub_scores=result.sub_scores,
            improvements=result.improvements,
            strengths=result.strengths,
            gaps=result.gaps,
        )
