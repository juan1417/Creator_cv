---
name: creador-de-cv
description: Entrevista a la persona candidata para recopilar y organizar la información profesional de un currículum vitae. Construye una estructura de CV clara en JSON y una versión final en Markdown. Use when the user asks to create, improve, organize, tailor, or translate a resume/CV.
---

# Creador de CV

## Objetivo

Guiar una entrevista profesional para crear y organizar un CV completo, claro y adaptado al perfil de la persona.

## Idioma de trabajo

1. Detectar idioma preferido del usuario: español, inglés o ambos.
2. Si el usuario no lo especifica, preguntar una sola vez.
3. Mantener consistencia de idioma en todo el proceso.

## Flujo guiado (obligatorio)

Sigue este orden y no saltes secciones sin confirmar:

1. Perfil objetivo
2. Experiencia laboral
3. Educación
4. Habilidades
5. Proyectos y logros
6. Idiomas y certificaciones
7. Revisión final y adaptación por puesto

En cada fase:
- Haz preguntas concretas y cortas.
- Resume lo entendido.
- Pide confirmación antes de continuar.

## Recolección mínima por sección

### 1) Perfil objetivo
- Puesto objetivo
- Área/industria
- Nivel (junior, semi-senior, senior, etc.)
- Ubicación y modalidad (remoto/híbrido/presencial)

### 2) Experiencia laboral
Para cada experiencia pedir:
- Cargo
- Empresa
- Fechas (inicio/fin)
- Responsabilidades clave (3-5)
- Logros medibles (cuando existan)
- Tecnologías/herramientas usadas

### 3) Educación
- Título
- Institución
- Fechas
- Enfoque o mención (si aplica)

### 4) Habilidades
Separar en:
- Habilidades técnicas
- Herramientas/plataformas
- Habilidades blandas

### 5) Proyectos y logros
- Nombre del proyecto/logro
- Contexto y objetivo
- Acciones realizadas
- Resultado medible

### 6) Idiomas y certificaciones
- Idioma + nivel
- Certificación + emisor + fecha

## Reglas de calidad

- Priorizar claridad y evidencia de impacto.
- Evitar texto genérico sin resultados.
- Convertir frases débiles en logros concretos cuando sea posible.
- Si faltan datos críticos, pedirlos explícitamente.
- No inventar información.

## Estructura de salida (entregar ambas)

Primero entregar JSON estructurado:

```json
{
  "target_role": "",
  "professional_summary": "",
  "experience": [
    {
      "role": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "responsibilities": [],
      "achievements": [],
      "technologies": []
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "start_date": "",
      "end_date": ""
    }
  ],
  "skills": {
    "technical": [],
    "tools": [],
    "soft": []
  },
  "projects": [
    {
      "name": "",
      "context": "",
      "actions": [],
      "results": []
    }
  ],
  "languages": [
    {
      "language": "",
      "level": ""
    }
  ],
  "certifications": [
    {
      "name": "",
      "issuer": "",
      "date": ""
    }
  ]
}
```

Luego entregar la versión final en Markdown:

```markdown
# Nombre Apellido
Cargo objetivo | Ciudad, País | Email | Teléfono | LinkedIn | Portafolio

## Professional Summary / Resumen Profesional
Breve resumen de 3-5 líneas enfocado al rol objetivo.

## Experience / Experiencia
### Cargo - Empresa
Fecha inicio - Fecha fin
- Responsabilidad o logro con impacto.
- Responsabilidad o logro con impacto.

## Education / Educación
### Título - Institución
Fecha inicio - Fecha fin

## Skills / Habilidades
- Technical / Técnicas:
- Tools / Herramientas:
- Soft / Blandas:

## Projects / Proyectos
### Nombre del proyecto
- Contexto:
- Acciones:
- Resultados:

## Languages / Idiomas
- Idioma - Nivel

## Certifications / Certificaciones
- Certificación - Emisor - Fecha
```

## Adaptación por vacante

Cuando el usuario comparta una oferta laboral:
1. Extraer keywords del puesto.
2. Reordenar experiencia y habilidades según relevancia.
3. Ajustar resumen profesional a esa vacante.
4. Señalar brechas (skills faltantes) sin inventar experiencia.

## Formato de interacción recomendado

Usar bloques breves:
- **Pregunta actual**
- **Información capturada**
- **Falta por completar**
- **Siguiente paso**

## Cierre

Antes de finalizar:
1. Validar que no falten fechas, cargos, empresas o educación.
2. Verificar consistencia de tiempos verbales y estilo.
3. Entregar:
   - JSON final del CV
   - CV final en Markdown
   - Versión adaptada a una vacante (si fue proporcionada)
