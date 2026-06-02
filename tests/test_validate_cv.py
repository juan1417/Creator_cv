"""Tests for ``creator_cv.schemas.validate_cv``."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from creator_cv.schemas import CVSchema, empty_cv, validate_cv


def test_empty_cv_is_valid():
    assert empty_cv()["experiencia"] == []
    assert empty_cv()["habilidades"]["tecnicas"] == []


def test_validate_minimal():
    data = {"meta": {"nombre_completo": "Ada"}}
    out = validate_cv(data)
    assert out["meta"]["nombre_completo"] == "Ada"
    assert out["experiencia"] == []
    assert out["habilidades"]["tecnicas"] == []


def test_validate_full():
    data = {
        "meta": {
            "nombre_completo": "Ada Lovelace",
            "titulo_profesional": "Mathematician",
            "contacto": {"email": "ada@example.com", "telefono": "0", "linkedin": "x", "ubicacion": "London"},
        },
        "perfil_profesional": {
            "resumen": "Pionera de la computación.",
            "palabras_clave": ["Matemáticas", "Computación"],
        },
        "experiencia": [
            {
                "empresa": "Acme",
                "cargo": "Lead",
                "ubicacion": "London",
                "fecha_inicio": "2020-01",
                "fecha_fin": "2023-12",
                "actual": False,
                "responsabilidades": ["Diseñar", "Implementar"],
                "logros": ["Reducir latencia 30%"],
            }
        ],
        "educacion": [
            {"institucion": "MIT", "titulo": "BSc", "estado": "Completado"}
        ],
        "habilidades": {
            "tecnicas": ["Python", "SQL"],
            "blandas": ["Liderazgo"],
            "idiomas": ["Inglés"],
        },
        "proyectos": [
            {"nombre": "MyApp", "descripcion": "Cool", "tecnologias": ["Python"], "enlace": "https://x"}
        ],
        "certificaciones": ["AWS Architect"],
        "fortalezas": ["Resiliencia"],
    }
    out = validate_cv(data)
    assert out["meta"]["nombre_completo"] == "Ada Lovelace"
    assert len(out["experiencia"]) == 1
    assert out["experiencia"][0]["empresa"] == "Acme"
    assert out["experiencia"][0]["responsabilidades"] == ["Diseñar", "Implementar"]
    assert out["habilidades"]["tecnicas"] == ["Python", "SQL"]
    assert out["proyectos"][0]["enlace"] == "https://x"


def test_defaults_fill_missing_optional():
    out = validate_cv({})
    assert out["meta"]["nombre_completo"] == ""
    assert out["perfil_profesional"] == {"resumen": "", "palabras_clave": []}
    assert out["habilidades"] == {"tecnicas": [], "blandas": [], "idiomas": []}


def test_invalid_type_raises():
    with pytest.raises(ValidationError):
        # experiencia must be a list, not a string
        validate_cv({"experiencia": "not a list"})


def test_invalid_nested_type_raises():
    with pytest.raises(ValidationError):
        # meta must be a dict, not a list
        validate_cv({"meta": ["invalid"]})


def test_schema_json_schema_is_dict():
    """The schema can be exported as a dict (for Gemini response_json_schema)."""
    js = CVSchema.model_json_schema()
    assert isinstance(js, dict)
    assert "properties" in js
    assert "experiencia" in js["properties"]
    assert "meta" in js["properties"]


def test_actual_default_false():
    out = validate_cv({"experiencia": [{"empresa": "A", "cargo": "B"}]})
    assert out["experiencia"][0]["actual"] is False


def test_chip_field_rejects_string():
    """Pydantic v2 does NOT coerce a single string to a list — must be a list."""
    with pytest.raises(ValidationError):
        validate_cv({"habilidades": {"tecnicas": "Python"}})  # type: ignore[arg-type]
