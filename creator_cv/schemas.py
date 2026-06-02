"""Pydantic schemas for the CV document.

The :class:`CVSchema` is the single source of truth for the structure
of a CV. It is used to:

* Validate form input before persisting (``validate_cv``).
* Force Gemini's structured output via ``response_json_schema``.
* Provide a clean dict for the renderers (PDF, DOCX, HTML).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError


class Contacto(BaseModel):
    email: str | None = None
    telefono: str | None = None
    linkedin: str | None = None
    ubicacion: str | None = None


class Meta(BaseModel):
    nombre_completo: str = ""
    titulo_profesional: str | None = None
    contacto: Contacto = Field(default_factory=Contacto)


class Perfil(BaseModel):
    resumen: str = ""
    palabras_clave: list[str] = Field(default_factory=list)


class Experiencia(BaseModel):
    empresa: str = ""
    cargo: str = ""
    ubicacion: str | None = None
    fecha_inicio: str = ""
    fecha_fin: str = ""
    actual: bool = False
    responsabilidades: list[str] = Field(default_factory=list)
    logros: list[str] = Field(default_factory=list)


class Educacion(BaseModel):
    institucion: str = ""
    titulo: str = ""
    ubicacion: str | None = None
    fecha_inicio: str = ""
    fecha_fin: str = ""
    estado: str | None = None


class Habilidades(BaseModel):
    tecnicas: list[str] = Field(default_factory=list)
    blandas: list[str] = Field(default_factory=list)
    idiomas: list[str] = Field(default_factory=list)


class Proyecto(BaseModel):
    nombre: str = ""
    descripcion: str = ""
    tecnologias: list[str] = Field(default_factory=list)
    enlace: str | None = None


class CVSchema(BaseModel):
    meta: Meta = Field(default_factory=Meta)
    perfil_profesional: Perfil = Field(default_factory=Perfil)
    experiencia: list[Experiencia] = Field(default_factory=list)
    educacion: list[Educacion] = Field(default_factory=list)
    habilidades: Habilidades = Field(default_factory=Habilidades)
    proyectos: list[Proyecto] = Field(default_factory=list)
    certificaciones: list[str] = Field(default_factory=list)
    fortalezas: list[str] = Field(default_factory=list)


def empty_cv() -> dict[str, Any]:
    """Return a fresh empty CV dict (useful for the new-CV form)."""
    return CVSchema().model_dump()


def validate_cv(data: dict[str, Any]) -> dict[str, Any]:
    """Validate ``data`` against :class:`CVSchema` and return a clean dict.

    Missing optional fields are filled with defaults. Raises
    :class:`pydantic.ValidationError` on bad input.
    """
    return CVSchema.model_validate(data).model_dump()


__all__ = [
    "Contacto",
    "Meta",
    "Perfil",
    "Experiencia",
    "Educacion",
    "Habilidades",
    "Proyecto",
    "CVSchema",
    "empty_cv",
    "validate_cv",
    "ValidationError",
]
