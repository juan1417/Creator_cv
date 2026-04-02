"""
Inserta un CV de demostración con **persona y trayectoria ficticias** (solo para pruebas).

Ejecutar desde la raíz del repo:
  uv run python -m creator_cv.seed_prueba

El CV se asocia al usuario `dev@local` (el mismo que usa la web por defecto).
"""

from __future__ import annotations

import json

from sqlalchemy import select

from creator_cv import create_app
from creator_cv.extensions import db
from creator_cv.models import CV, User

CV_TITLE = "Demostración — Lena Martínez (persona ficticia)"

# Datos inventados explícitamente para pruebas; no usar como CV real.
CONTEXT: dict = {
    "meta": {
        "idioma_cv": "es",
        "nombre_completo": "Lena Martínez (persona ficticia)",
        "titulo_profesional": "Desarrolladora backend | Python y APIs",
        "objetivo_cv": "[Demo] Backend Python en entorno de pruebas — rol ficticio.",
        "tipo_cv": "cronológico",
        "nivel_seniority": "semi-senior",
        "contacto": {
            "telefono": "+34 000 000 000 (demo)",
            "email": "lena.demo@example.invalid",
            "linkedin": "linkedin.com/in/ejemplo-demo",
            "ubicacion": "Remoto, UE (ficticio)",
        },
    },
    "certificaciones": [
        {
            "nombre": "Certificación demo Cloud (ficticia)",
            "descripcion": "Ejemplo de título breve para probar la columna izquierda.",
        }
    ],
    "fortalezas": [
        {
            "titulo": "Diseño de APIs",
            "descripcion": "Contratos REST de ejemplo en proyectos de laboratorio.",
        },
        {
            "titulo": "Código mantenible",
            "descripcion": "Revisiones y pruebas simuladas en equipo ficticio.",
        },
    ],
    "perfil_profesional": {
        "resumen": (
            "Personaje ficticio para probar Creator CV. "
            "Desarrolladora backend de ejemplo en sector demo."
        ),
        "palabras_clave": ["Python", "Flask", "PostgreSQL", "APIs REST"],
    },
    "experiencia": [
        {
            "empresa": "Empresa Demo S.A. (ficticia)",
            "cargo": "Desarrolladora backend",
            "ubicacion": "Remoto (demo)",
            "fecha_inicio": "2022-01",
            "fecha_fin": "",
            "actual": True,
            "responsabilidades": [
                "Mantenimiento de APIs de ejemplo en entorno de prueba.",
                "Revisión de código simulada entre compañeros ficticios.",
            ],
            "logros": [
                "Reducción de latencia en entorno de laboratorio (métrica de demo).",
            ],
        },
        {
            "empresa": "Startup Ejemplo Labs (ficticia)",
            "cargo": "Junior developer",
            "ubicacion": "Ciudad Demo",
            "fecha_inicio": "2020-06",
            "fecha_fin": "2021-12",
            "actual": False,
            "responsabilidades": [
                "Scripts internos de prueba y automatización ficticia.",
            ],
            "logros": [],
        },
    ],
    "educacion": [
        {
            "institucion": "Universidad Ficticia de Ejemplolandia",
            "titulo": "Grado en Ingeniería Informática (demo)",
            "ubicacion": "",
            "fecha_inicio": "2016",
            "fecha_fin": "2020",
            "estado": "completo",
        }
    ],
    "habilidades": {
        "tecnicas": ["Python", "SQL", "Git", "Docker (básico demo)"],
        "blandas": ["Comunicación", "Trabajo en equipo"],
        "idiomas": ["Español nativo", "Inglés B2 (ejemplo)"],
    },
    "proyectos": [
        {
            "nombre": "Proyecto Demo CV",
            "descripcion": "Aplicación de ejemplo para validar exportación Markdown/PDF.",
            "tecnologias": ["Flask", "SQLite"],
            "enlace": "",
        }
    ],
    "recursos_actuales": {
        "cv_existente": False,
        "texto_cv": "",
        "links": [],
    },
    "restricciones": {
        "extension_maxima_paginas": 2,
        "formato_solicitado": "PDF",
        "otro": "Dataset solo para pruebas locales.",
    },
    "dudas_pendientes": [
        "Confirmar fechas exactas si este CV pasara a datos reales (ahora son de ejemplo).",
    ],
}

REVIEW_DEMO = """# Revisión de demostración (ficticia)

Este bloque es **solo de prueba** para la entrevista MCP / revisión en la web.

- Objetivo declarado: rol backend de ejemplo.
- Experiencias y centros son inventados para poblar la interfaz.
"""


def main() -> None:
    app = create_app()
    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == "dev@local"))
        if user is None:
            user = User(email="dev@local", password_hash=None)
            db.session.add(user)
            db.session.flush()

        existing = db.session.scalar(
            select(CV).where(CV.user_id == user.id, CV.title == CV_TITLE)
        )
        if existing is not None:
            print(f"Ya existe el CV de prueba (id={existing.id}). No se duplica.")
            return

        cv = CV(
            user_id=user.id,
            title=CV_TITLE,
            context_json=json.dumps(CONTEXT, ensure_ascii=False, indent=2),
            review_markdown=REVIEW_DEMO,
        )
        db.session.add(cv)
        db.session.commit()
        print(f"CV de prueba creado: id={cv.id}, título={CV_TITLE!r}")
        print("Abre la app y revisa la lista en /")


if __name__ == "__main__":
    main()
