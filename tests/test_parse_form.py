"""Tests for ``creator_cv.form_parser.parse_form_to_cv``."""

from __future__ import annotations

from creator_cv.form_parser import parse_form_to_cv


def test_empty_form_returns_empty_sections():
    cv = parse_form_to_cv({})
    assert cv["experiencia"] == []
    assert cv["educacion"] == []
    assert cv["proyectos"] == []
    assert cv["habilidades"]["tecnicas"] == []
    assert cv["certificaciones"] == []


def test_meta_and_contact():
    cv = parse_form_to_cv(
        {
            "meta.nombre_completo": "Ada Lovelace",
            "meta.titulo_profesional": "Mathematician",
            "meta.contacto.email": "ada@example.com",
            "meta.contacto.telefono": "+44 0",
            "meta.contacto.linkedin": "linkedin.com/in/ada",
            "meta.contacto.ubicacion": "London",
        }
    )
    assert cv["meta"]["nombre_completo"] == "Ada Lovelace"
    assert cv["meta"]["titulo_profesional"] == "Mathematician"
    assert cv["meta"]["contacto"]["email"] == "ada@example.com"
    assert cv["meta"]["contacto"]["ubicacion"] == "London"


def test_experiencia_indexed():
    cv = parse_form_to_cv(
        {
            "experiencia[0][empresa]": "Acme",
            "experiencia[0][cargo]": "Lead",
            "experiencia[0][fecha_inicio]": "2020",
            "experiencia[0][fecha_fin]": "2023",
            "experiencia[0][actual]": "on",
            "experiencia[0][responsabilidades]": "Line 1\nLine 2\n\nLine 3",
            "experiencia[1][empresa]": "Globex",
            "experiencia[1][cargo]": "Engineer",
        }
    )
    assert len(cv["experiencia"]) == 2
    assert cv["experiencia"][0]["empresa"] == "Acme"
    assert cv["experiencia"][0]["actual"] is True
    assert cv["experiencia"][0]["responsabilidades"] == ["Line 1", "Line 2", "Line 3"]
    assert cv["experiencia"][1]["empresa"] == "Globex"


def test_educacion_indexed():
    cv = parse_form_to_cv(
        {
            "educacion[0][institucion]": "MIT",
            "educacion[0][titulo]": "BSc CS",
            "educacion[0][estado]": "Completado",
        }
    )
    assert cv["educacion"][0]["institucion"] == "MIT"
    assert cv["educacion"][0]["titulo"] == "BSc CS"


def test_proyectos_with_tecnologias_csv():
    cv = parse_form_to_cv(
        {
            "proyectos[0][nombre]": "MyApp",
            "proyectos[0][descripcion]": "Cool app",
            "proyectos[0][tecnologias]": "Python, Flask, SQLite",
            "proyectos[0][enlace]": "https://example.com",
        }
    )
    assert cv["proyectos"][0]["tecnologias"] == ["Python", "Flask", "SQLite"]
    assert cv["proyectos"][0]["enlace"] == "https://example.com"


def test_habilidades_chips():
    from werkzeug.datastructures import MultiDict
    form = MultiDict([
        ("habilidades[tecnicas][]", "Python"),
        ("habilidades[tecnicas][]", "Flask"),
        ("habilidades[blandas][]", "Comunicación"),
        ("habilidades[idiomas][]", "Español"),
        ("habilidades[idiomas][]", "Inglés"),
    ])
    cv = parse_form_to_cv(form)
    assert cv["habilidades"]["tecnicas"] == ["Python", "Flask"]
    assert cv["habilidades"]["blandas"] == ["Comunicación"]
    assert cv["habilidades"]["idiomas"] == ["Español", "Inglés"]


def test_certificaciones_and_fortalezas_chips():
    from werkzeug.datastructures import MultiDict
    form = MultiDict([
        ("certificaciones[items][]", "AWS Architect"),
        ("certificaciones[items][]", "PMP"),
        ("fortalezas[items][]", "Liderazgo"),
    ])
    cv = parse_form_to_cv(form)
    assert cv["certificaciones"] == ["AWS Architect", "PMP"]
    assert cv["fortalezas"] == ["Liderazgo"]


def test_palabras_clave_csv():
    cv = parse_form_to_cv(
        {"perfil_profesional.palabras_clave": "Python, Flask, AWS, "}
    )
    assert cv["perfil_profesional"]["palabras_clave"] == ["Python", "Flask", "AWS"]


def test_actual_checkbox_only_truthy_when_on():
    cv = parse_form_to_cv({"experiencia[0][actual]": "on"})
    assert cv["experiencia"][0]["actual"] is True

    cv2 = parse_form_to_cv({})  # no checkbox
    assert cv2["experiencia"] == []


def test_empty_fields_become_empty_strings_or_none():
    cv = parse_form_to_cv({"meta.titulo_profesional": ""})
    assert cv["meta"]["titulo_profesional"] is None
