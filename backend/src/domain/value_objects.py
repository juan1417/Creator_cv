"""Value objects: objetos inmutables definidos por sus atributos.

No tienen identidad, son intercambiables si tienen los mismos valores.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContactInfo:
    """Datos de contacto de un CV. Validado."""

    telefono: str = ""
    email: str = ""
    linkedin: str = ""
    ubicacion: str = ""

    def __post_init__(self) -> None:
        if self.email and "@" not in self.email:
            raise ValueError(f"email inválido: {self.email!r}")


@dataclass(frozen=True)
class CVContext:
    """Context tipado del CV. Se serializa como JSON en la DB.

    Es value object porque se identifica por su contenido, no por su id.
    """

    meta: dict[str, Any]
    certificaciones: list[dict[str, Any]]
    fortalezas: list[dict[str, Any]]
    perfil_profesional: dict[str, Any]
    experiencia: list[dict[str, Any]]
    educacion: list[dict[str, Any]]
    habilidades: dict[str, Any]
    proyectos: list[dict[str, Any]]
    recursos_actuales: dict[str, Any]
    restricciones: dict[str, Any]
    dudas_pendientes: list[str]

    def to_json(self) -> str:
        import json
        return json.dumps(self._to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, raw: str) -> CVContext:
        import json
        data = json.loads(raw)
        return cls.from_dict(data)

    def _to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta,
            "certificaciones": self.certificaciones,
            "fortalezas": self.fortalezas,
            "perfil_profesional": self.perfil_profesional,
            "experiencia": self.experiencia,
            "educacion": self.educacion,
            "habilidades": self.habilidades,
            "proyectos": self.proyectos,
            "recursos_actuales": self.recursos_actuales,
            "restricciones": self.restricciones,
            "dudas_pendientes": self.dudas_pendientes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CVContext:
        """Construye un CVContext desde un dict, con valores por defecto seguros."""
        return cls(
            meta=data.get("meta") or {},
            certificaciones=data.get("certificaciones") or [],
            fortalezas=data.get("fortalezas") or [],
            perfil_profesional=data.get("perfil_profesional") or {},
            experiencia=data.get("experiencia") or [],
            educacion=data.get("educacion") or [],
            habilidades=data.get("habilidades") or {},
            proyectos=data.get("proyectos") or [],
            recursos_actuales=data.get("recursos_actuales") or {},
            restricciones=data.get("restricciones") or {},
            dudas_pendientes=data.get("dudas_pendientes") or [],
        )

    @classmethod
    def empty(cls) -> CVContext:
        return cls.from_dict({})
