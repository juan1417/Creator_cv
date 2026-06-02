"""Tests for ``creator_cv.match_scorer``."""

from __future__ import annotations

from creator_cv.match_scorer import (
    badge_color,
    extract_keywords,
    score_match,
)


def _cv(**overrides):
    base = {
        "meta": {"nombre_completo": "Test", "titulo_profesional": "Dev"},
        "habilidades": {
            "tecnicas": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
            "blandas": [],
            "idiomas": ["Inglés B2", "Español nativo"],
        },
        "experiencia": [
            {
                "empresa": "A",
                "cargo": "Dev",
                "fecha_inicio": "2020-01",
                "fecha_fin": "2024-01",
                "actual": False,
                "responsabilidades": [],
                "logros": [],
            },
            {
                "empresa": "B",
                "cargo": "Senior",
                "fecha_inicio": "2017-01",
                "fecha_fin": "2019-12",
                "actual": False,
                "responsabilidades": [],
                "logros": [],
            },
        ],
        "educacion": [],
        "proyectos": [],
    }
    base.update(overrides)
    return base


def test_score_full_match_returns_high():
    offer = "Buscamos Senior Backend con 3+ años de experiencia en Python, FastAPI, PostgreSQL, Docker y AWS. Inglés B2."
    r = score_match(_cv(), offer)
    assert r["total"] >= 90
    assert r["dimensions"]["tecnicas"]["score"] == 60
    assert r["dimensions"]["idiomas"]["score"] == 20
    assert r["dimensions"]["experiencia"]["score"] == 20
    assert r["dimensions"]["tecnicas"]["missing"] == []


def test_score_no_match_returns_low():
    offer = "Buscamos Frontend Developer React con TypeScript y Next.js. 5 años de experiencia."
    r = score_match(_cv(), offer)
    # Some credit for years (cv has 6 >= 5), but 0 for skills.
    assert r["dimensions"]["tecnicas"]["score"] == 0
    assert r["dimensions"]["tecnicas"]["missing"]  # has missing
    assert r["total"] <= 30


def test_score_without_offer_returns_zero_or_skeleton():
    r = score_match(_cv(), "")
    # No required techs → 0; no required langs → 0; no required years → 10
    # (because years > 0).
    assert r["total"] == 10
    assert r["dimensions"]["tecnicas"]["score"] == 0
    assert r["dimensions"]["idiomas"]["score"] == 0


def test_score_partial_match():
    offer = "Necesitamos Python, requerido Java, plus Kubernetes."
    r = score_match(_cv(), offer)
    # 1 of 3 known techs in CV.
    assert r["dimensions"]["tecnicas"]["score"] < 60
    assert "python" in r["dimensions"]["tecnicas"]["matched"]
    assert "java" in r["dimensions"]["tecnicas"]["missing"]


def test_badge_color_thresholds():
    assert badge_color(100) == "badge-green"
    assert badge_color(75) == "badge-green"
    assert badge_color(74) == "badge-yellow"
    assert badge_color(50) == "badge-yellow"
    assert badge_color(49) == "badge-orange"
    assert badge_color(25) == "badge-orange"
    assert badge_color(24) == "badge-red"
    assert badge_color(0) == "badge-red"


def test_extract_keywords_dedupes_and_lowercases():
    kws = extract_keywords("Python, python, PYTHON, Java")
    assert "python" in kws
    assert kws.count("python") == 1
    assert "java" in kws


def test_score_handles_empty_cv_gracefully():
    empty = {
        "meta": {},
        "habilidades": {"tecnicas": [], "blandas": [], "idiomas": []},
        "experiencia": [],
        "educacion": [],
        "proyectos": [],
    }
    r = score_match(empty, "Buscamos Python developer con 3 años de experiencia.")
    # With empty CV, score must be 0; "python" must appear in missing.
    assert r["total"] == 0
    assert "python" in r["dimensions"]["tecnicas"]["missing"]


def test_score_summary_format():
    offer = "Buscamos Python, FastAPI, PostgreSQL, Docker, AWS. 3 años."
    r = score_match(_cv(), offer)
    # "5/5 skills" is present
    assert "skills" in r["summary"]


def test_score_with_proyecto_tecnologias():
    cv = _cv()
    cv["proyectos"] = [
        {
            "nombre": "X",
            "descripcion": "",
            "tecnologias": ["Kubernetes", "Terraform"],
            "enlace": "",
        }
    ]
    offer = "Buscamos experiencia con Kubernetes y Terraform."
    r = score_match(cv, offer)
    assert r["dimensions"]["tecnicas"]["score"] == 60
