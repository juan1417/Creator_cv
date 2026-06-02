"""Tests for ``creator_cv.gemini_adapter.adapt_until_score``.

We mock the underlying Gemini client to make the test deterministic
and to assert the loop's behavior: feedback is sent on iterations > 1,
the best CV is returned, and ``reached_target`` is computed correctly.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from creator_cv import gemini_adapter


def _mock_client_factory(adapted_cvs: list[dict], review_text: str = "- Sugerencia 1\n- Sugerencia 2"):
    """Build a fake ``genai.Client`` that returns ``adapted_cvs[i]`` on the i-th call.

    Also patches ``score_match`` indirectly by feeding pre-baked CVs that
    have known match scores.
    """
    state = {"call": 0}

    class FakeModels:
        def generate_content(self, *args, **kwargs):
            state["call"] += 1
            import json
            from google.genai import types

            # Detect adapt vs review by config.response_mime_type
            mime = kwargs.get("config") or types.GenerateContentConfig()
            mime_type = getattr(mime, "response_mime_type", None) or (
                mime.get("response_mime_type") if isinstance(mime, dict) else None
            )
            if mime_type == "application/json":
                idx = min(state["call"] - 1, len(adapted_cvs) - 1)
                return _FakeResponse(json.dumps(adapted_cvs[idx]))
            return _FakeResponse(review_text)

    class FakeClient:
        def __init__(self, *a, **kw):
            pass

        models = FakeModels()

    return FakeClient(), state


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text


def _patch_client(factory):
    return patch.object(gemini_adapter, "_get_client", return_value=factory)


def test_loop_stops_when_target_reached():
    """If iteration 1 already passes the target, the loop returns immediately."""
    cv = {
        "meta": {"nombre_completo": "A", "contacto": {}},
        "perfil_profesional": {"resumen": "", "palabras_clave": []},
        "habilidades": {"tecnicas": ["python", "fastapi"], "blandas": [], "idiomas": []},
        "experiencia": [
            {
                "empresa": "A",
                "cargo": "Dev",
                "fecha_inicio": "2020-01",
                "fecha_fin": "2024-01",
                "actual": False,
                "responsabilidades": ["Python", "FastAPI"],
                "logros": [],
            }
        ],
        "educacion": [],
        "proyectos": [],
        "certificaciones": [],
        "fortalezas": [],
    }
    offer = "Buscamos Python FastAPI developer."
    # Iteration 1 already returns a CV with all skills — score ~60+ of 60 techs.
    fake_client, state = _mock_client_factory([cv])
    with _patch_client(fake_client):
        adapted, review, meta = gemini_adapter.adapt_until_score(
            cv, offer, target_score=70, max_iterations=5
        )
    assert meta["iterations"] == 1
    assert meta["reached_target"] is True
    assert meta["final_score"] >= 60
    # Only 2 calls: 1 adapt + 1 review.
    assert state["call"] == 2


def test_loop_iterates_and_uses_feedback():
    """If the first iteration is weak, the loop sends a feedback prompt with missing items."""
    weak_cv = {
        "meta": {"nombre_completo": "A", "contacto": {}},
        "perfil_profesional": {"resumen": "", "palabras_clave": []},
        "habilidades": {"tecnicas": [], "blandas": [], "idiomas": []},
        "experiencia": [
            {
                "empresa": "A",
                "cargo": "Dev",
                "fecha_inicio": "2020-01",
                "fecha_fin": "2024-01",
                "actual": False,
                "responsabilidades": ["Excel"],
                "logros": [],
            }
        ],
        "educacion": [],
        "proyectos": [],
        "certificaciones": [],
        "fortalezas": [],
    }
    strong_cv = {
        "meta": {"nombre_completo": "A", "contacto": {}},
        "perfil_profesional": {"resumen": "", "palabras_clave": []},
        "habilidades": {
            "tecnicas": ["python", "fastapi", "docker", "aws", "kubernetes"],
            "blandas": [],
            "idiomas": [],
        },
        "experiencia": [
            {
                "empresa": "A",
                "cargo": "Dev",
                "fecha_inicio": "2020-01",
                "fecha_fin": "2024-01",
                "actual": False,
                "responsabilidades": ["Python", "FastAPI", "Docker", "AWS", "Kubernetes"],
                "logros": [],
            }
        ],
        "educacion": [],
        "proyectos": [],
        "certificaciones": [],
        "fortalezas": [],
    }
    offer = "Buscamos Python, FastAPI, Docker, AWS, Kubernetes. 3 años."
    # We capture the prompts sent to Gemini to verify iteration 2 uses
    # ITERATION_FEEDBACK_PROMPT (which mentions "anterior").
    captured_prompts: list[str] = []

    class FakeModels:
        def __init__(self):
            self.call = 0
        def generate_content(self, contents, **kwargs):
            self.call += 1
            import json
            from google.genai import types
            if isinstance(contents, list):
                captured_prompts.append(contents[0])
            else:
                captured_prompts.append(str(contents))
            mime = kwargs.get("config") or types.GenerateContentConfig()
            mime_type = getattr(mime, "response_mime_type", None) or (
                mime.get("response_mime_type") if isinstance(mime, dict) else None
            )
            if mime_type == "application/json":
                if self.call == 1:
                    return _FakeResponse(json.dumps(weak_cv))
                return _FakeResponse(json.dumps(strong_cv))
            return _FakeResponse("- review")

    class FakeClient:
        def __init__(self, *a, **kw): pass
        models = FakeModels()

    with patch.object(gemini_adapter, "_get_client", return_value=FakeClient()):
        adapted, review, meta = gemini_adapter.adapt_until_score(
            weak_cv, offer, target_score=70, max_iterations=5
        )
    assert meta["iterations"] >= 2
    assert meta["reached_target"] is True
    # Second prompt must mention "anterior" (feedback loop).
    assert any("anterior" in p for p in captured_prompts[1:])


def test_loop_returns_best_when_target_not_reached():
    """If the loop never reaches the target, it returns the best CV found."""
    cv = {
        "meta": {"nombre_completo": "A", "contacto": {}},
        "perfil_profesional": {"resumen": "", "palabras_clave": []},
        "habilidades": {"tecnicas": [], "blandas": [], "idiomas": []},
        "experiencia": [],
        "educacion": [],
        "proyectos": [],
        "certificaciones": [],
        "fortalezas": [],
    }
    # CV that has SOME skills but never reaches 70
    partial = dict(cv)
    partial["habilidades"] = {"tecnicas": ["python"], "blandas": [], "idiomas": []}
    offer = "Buscamos Python, FastAPI, Docker, Kubernetes, AWS, Terraform, Redis, GraphQL. 5 años."
    fake_client, state = _mock_client_factory([partial] * 5)
    with _patch_client(fake_client):
        adapted, review, meta = gemini_adapter.adapt_until_score(
            cv, offer, target_score=70, max_iterations=3
        )
    # 1 of 8 known techs = 60 * (1/8) = 7.5 → 8. Plus partial credit for 0 years.
    # Should NOT reach 70.
    assert meta["reached_target"] is False
    assert meta["iterations"] == 3
    assert meta["final_score"] < 70
    # Should still return *some* CV (the partial one).
    assert adapted["habilidades"]["tecnicas"] == ["python"]


def test_loop_progress_callback():
    """The on_progress callback is called once per iteration."""
    weak_cv = {
        "meta": {"nombre_completo": "A", "contacto": {}},
        "perfil_profesional": {"resumen": "", "palabras_clave": []},
        "habilidades": {"tecnicas": [], "blandas": [], "idiomas": []},
        "experiencia": [],
        "educacion": [],
        "proyectos": [],
        "certificaciones": [],
        "fortalezas": [],
    }
    # Empty CV: never matches 9 required skills, so we hit max_iterations.
    offer = "Buscamos Python, FastAPI, Docker, Kubernetes, AWS, Terraform, Redis, GraphQL, Java. 5 años."
    fake_client, _ = _mock_client_factory([weak_cv] * 3)
    calls: list[tuple[int, int, int]] = []
    with _patch_client(fake_client):
        gemini_adapter.adapt_until_score(
            weak_cv, offer, target_score=90, max_iterations=3,
            on_progress=lambda it, score, total: calls.append((it, score, total)),
        )
    assert len(calls) == 3
    assert [c[0] for c in calls] == [1, 2, 3]


# --- improve_cv tests -----------------------------------------------------


def test_improve_cv_returns_valid_dict():
    """improve_cv() calls Gemini and returns a validated CV dict."""
    cv = {
        "meta": {"nombre_completo": "A", "contacto": {}},
        "perfil_profesional": {"resumen": "old", "palabras_clave": []},
        "habilidades": {"tecnicas": ["Python"], "blandas": [], "idiomas": []},
        "experiencia": [
            {
                "empresa": "X",
                "cargo": "Dev",
                "fecha_inicio": "2020-01",
                "fecha_fin": "2024-01",
                "actual": False,
                "responsabilidades": ["Hice cosas"],
                "logros": [],
            }
        ],
        "educacion": [],
        "proyectos": [],
        "certificaciones": [],
        "fortalezas": [],
    }
    # The improved CV has stronger resumen and a bullet starting with action verb.
    improved = {
        "meta": {"nombre_completo": "A", "contacto": {}},
        "perfil_profesional": {
            "resumen": "Backend con 4 años de experiencia. Especializado en APIs REST.",
            "palabras_clave": ["Python", "APIs"],
        },
        "habilidades": {"tecnicas": ["Python", "APIs"], "blandas": [], "idiomas": []},
        "experiencia": [
            {
                "empresa": "X",
                "cargo": "Dev",
                "fecha_inicio": "2020-01",
                "fecha_fin": "2024-01",
                "actual": False,
                "responsabilidades": [
                    "Diseñé APIs REST usadas por 50K usuarios",
                    "Lideré migración a microservicios reduciendo latencia",
                ],
                "logros": ["Aumenté el engagement un 30%"],
            }
        ],
        "educacion": [],
        "proyectos": [],
        "certificaciones": [],
        "fortalezas": ["Resolución de problemas complejos"],
    }
    fake_client, _ = _mock_client_factory([improved])
    with _patch_client(fake_client):
        out = gemini_adapter.improve_cv(cv)
    assert out["perfil_profesional"]["resumen"] != "old"
    assert any(
        r.startswith(("Diseñé", "Lideré", "Implementé", "Optimizé", "Reduje"))
        for r in out["experiencia"][0]["responsabilidades"]
    )


def test_improve_cv_raises_if_gemini_returns_invalid():
    """If Gemini returns something that fails pydantic validation, raise RuntimeError."""
    from pydantic import ValidationError

    cv = {
        "meta": {"nombre_completo": "A", "contacto": {}},
        "perfil_profesional": {"resumen": "", "palabras_clave": []},
        "habilidades": {"tecnicas": [], "blandas": [], "idiomas": []},
        "experiencia": [],
        "educacion": [],
        "proyectos": [],
        "certificaciones": [],
        "fortalezas": [],
    }
    # Bad response: experiencia should be a list, not a string.
    bad = dict(cv)
    bad["experiencia"] = "not a list"

    # Patch _call_json to return the bad dict, and skip validation retries.
    class FakeModels:
        def generate_content(self, *a, **kw):
            return _FakeResponse(__import__("json").dumps(bad))
    class FakeClient:
        models = FakeModels()
    with patch.object(gemini_adapter, "_get_client", return_value=FakeClient()):
        with pytest.raises((ValidationError, RuntimeError)):
            gemini_adapter.improve_cv(cv)
