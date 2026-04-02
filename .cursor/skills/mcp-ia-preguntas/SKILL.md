---
name: mcp-ia-preguntas
description: Entrevista al usuario usando una IA (vía MCP o modelo integrado) para crear o mejorar un currículum vitae. Genera preguntas de clarificación, mantiene un contexto estructurado sobre lo que la persona quiere y lo que ya tiene, y devuelve tanto JSON como Markdown. Usar cuando el usuario quiera crear, refinar, adaptar o traducir un CV o perfil profesional y se necesite recopilar información mediante preguntas.
---

# MCP IA Preguntas para CV

Este skill guía a la IA para **entrevistar al usuario** y construir un **contexto completo de CV/perfil profesional**, usando preguntas iterativas y manteniendo una representación estructurada de la información.

## Objetivo

Cuando se use este skill, la IA debe:

1. Hacer preguntas inteligentes y progresivas para entender:
   - Lo que la persona **quiere lograr** con su CV (objetivo, tipo de rol, mercado, idioma, etc.).
   - Lo que la persona **ya tiene** (experiencia, formación, habilidades, logros, proyectos, enlaces).
2. Mantener un **contexto estructurado en JSON** que se vaya rellenando a medida que el usuario responde.
3. Generar una **versión en Markdown** del CV basada en ese JSON.

Este skill está pensado para usarse desde comandos tipo `/mcp-ia-preguntas` o cuando el usuario hable de integrar una IA/MCP para hacer preguntas sobre su CV.

## Flujo de trabajo recomendado

Sigue siempre este flujo, ajustándolo según las respuestas del usuario:

1. **Arranque de la entrevista**
   - Explica brevemente el proceso al usuario (preguntas cortas, varias rondas, resultado en CV).
   - Pregunta primero por el **objetivo principal** del CV.
   - Pregunta por el **idioma preferido** del CV (ej. español, inglés).

2. **Construcción del contexto (JSON)**
   - Mantén un objeto JSON con esta forma aproximada:

```json
{
  "meta": {
    "idioma_cv": "es",
    "objetivo_cv": "postular a puesto de desarrollador backend",
    "tipo_cv": "cronologico | funcional | mixto",
    "nivel_seniority": "junior | semi-senior | senior | liderazgo"
  },
  "perfil_profesional": {
    "resumen": "",
    "palabras_clave": []
  },
  "experiencia": [
    {
      "empresa": "",
      "cargo": "",
      "ubicacion": "",
      "fecha_inicio": "",
      "fecha_fin": "",
      "actual": false,
      "responsabilidades": [],
      "logros": []
    }
  ],
  "educacion": [
    {
      "institucion": "",
      "titulo": "",
      "ubicacion": "",
      "fecha_inicio": "",
      "fecha_fin": "",
      "estado": "completo | en curso"
    }
  ],
  "habilidades": {
    "tecnicas": [],
    "blandas": [],
    "idiomas": []
  },
  "proyectos": [
    {
      "nombre": "",
      "descripcion": "",
      "tecnologias": [],
      "enlace": ""
    }
  ],
  "recursos_actuales": {
    "cv_existente": false,
    "texto_cv": "",
    "links": []
  },
  "restricciones": {
    "extension_maxima_paginas": null,
    "formato_solicitado": "",
    "otro": ""
  },
  "dudas_pendientes": []
}
```

   - No es obligatorio rellenar todos los campos, pero sí mantener la estructura general.
   - A medida que el usuario responde, **actualiza mentalmente** este JSON y úsalo como referencia para las siguientes preguntas.

3. **Estrategia de preguntas**
   - Haz **pocas preguntas por mensaje** (1–3) y muy claras.
   - Prioriza este orden general (puede variar según contexto):
     1. Objetivo del CV y tipo de rol.
     2. Experiencia profesional clave.
     3. Habilidades técnicas y blandas.
     4. Formación/educación relevante.
     5. Proyectos y logros destacados.
     6. Restricciones de formato o empresa (ATS, plantilla, tamaño, idioma).
   - Cuando falten datos importantes, resúmelo en voz alta y pregunta explícitamente por esos huecos.

4. **Generación de salida**
   - Una vez que tengas suficiente información o el usuario diga que es suficiente, genera **dos salidas**:
     1. **JSON estructurado** con todo el contexto del usuario (siguiendo el esquema anterior lo mejor posible).
     2. **CV en Markdown** siguiendo el formato de la siguiente sección.

## Formato estándar de salida

### 1. Contexto en JSON

- Devuélvelo en un bloque de código con etiqueta `json`.
- Asegúrate de que sea **válido JSON** (sin comentarios, sin comas finales).

Ejemplo de encabezado:

```markdown
### Contexto estructurado (JSON)

```json
{ ... }
```
```

### 2. CV en Markdown

Usa esta plantilla base y adáptala:

```markdown
# [Nombre Apellido]
[Ciudad, País] · [Email] · [Teléfono] · [LinkedIn / GitHub / Portafolio]

## Perfil profesional
[Resumen de 3–5 líneas, orientado al objetivo del usuario.]

## Experiencia
- **[Cargo] – [Empresa]** · [Ubicación] · [Fecha inicio] – [Fecha fin o Actual]
  - [Responsabilidad o logro medible 1]
  - [Responsabilidad o logro medible 2]

## Educación
- **[Título] – [Institución]** · [Ubicación] · [Fecha inicio] – [Fecha fin o En curso]

## Habilidades
- **Técnicas**: [Lista separada por comas]
- **Blandas**: [Lista separada por comas]
- **Idiomas**: [Idioma (nivel), Idioma (nivel)]

## Proyectos
- **[Nombre del proyecto]**
  - [Descripción corta orientada a impacto]
  - Tecnologías: [lista]
  - Enlace: [URL si aplica]
```

Adapta secciones (por ejemplo, añadir `Certificaciones` o `Publicaciones`) según el contexto recogido.

## Uso con comandos y disparadores

- Este skill es especialmente útil cuando:
  - El usuario escriba comandos tipo **`/mcp-ia-preguntas`** o similar.
  - El usuario mencione integrar una IA/MCP para **hacer preguntas** y **crear o mejorar un CV**.
- En esos casos:
  - Sigue el flujo de entrevista descrito.
  - Evita generar el CV final hasta que tengas información razonablemente completa o el usuario lo solicite.

## Buenas prácticas

- Mantén siempre un tono **claro, profesional y empático**.
- Evita respuestas demasiado largas; prefiere ciclos de:
  - breve resumen del contexto actual,
  - 1–3 preguntas nuevas,
  - actualización del esquema mental (JSON),
  - y sólo al final, la generación del CV y el JSON completo.
- Si el usuario ya tiene un CV, pide que lo pegue o lo adjunte en texto y **úsalo como base**, corrigiendo estructura, claridad y enfoque.

