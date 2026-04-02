# Conexión MCP: IA Preguntas + contexto de CV

Esta carpeta acopla el flujo del skill **`.cursor/skills/mcp-ia-preguntas/SKILL.md`** con archivos de contexto que una IA puede **leer y escribir** mediante MCP.

## Estructura

| Ruta | Uso |
|------|-----|
| `context/cv-context.template.json` | Plantilla vacía; puedes copiarla a `cv-context.active.json`. |
| `context/cv-context.active.json` | Copia de trabajo (no versionar datos personales si subes el repo a Git público). |
| `context/cv-interview.pending.template.json` | Esquema de **una ronda** de entrevista para la web: la IA copia el formato a `cv-interview.pending.json` con la pregunta actual. |
| `context/cv-interview.pending.json` | Pregunta activa (la web lo muestra y lo elimina al guardar la respuesta). Opcional en git (suele estar ignorado). |
| `context/cv-review-cv<id>.active.md` | Espejo en disco del Markdown de revisión por CV (sustituye `<id>` por el número del CV en la web). |
| `prompts/interviewer-system.md` | Texto de rol para pegar en un asistente externo o como recordatorio de comportamiento. |
| `mcp.cursor.example.json` | Ejemplo de MCP en Cursor usando **solo Python + uv** (sin Node/npm). |

## Pasos en Cursor

1. Copia `context/cv-context.template.json` a `context/cv-context.active.json` y rellénalo en la medida en que avance la entrevista.
2. Instala dependencias MCP del repo (una vez): en la raíz de **Creator_cv** ejecuta `uv sync --group mcp`.
3. En la configuración MCP de Cursor, usa [`mcp.cursor.example.json`](mcp.cursor.example.json) como base:
   - Sustituye **`REPLACE_WITH_ABSOLUTE_PATH_TO_REPO`** por la ruta absoluta del repo (en Windows suele ser `C:/Users/.../Creator_cv`; usa barras `/` en JSON).
   - **Gemini:** en la raíz del repo crea/edita **`.env`** (ya está en `.gitignore`) con `GEMINI_API_KEY` y opcionalmente `GEMINI_MODEL`. El servidor `creator_cv.mcp.gemini_server` carga ese `.env` automáticamente. Alternativa: define la clave solo en `env` del MCP en Cursor (sin `.env`).
4. Servidores incluidos:
   - **`creator-cv-context`**: herramientas `read_text_file`, `write_text_file`, `list_directory` **solo** bajo `mcp-ia-preguntas/context` (equivalente al filesystem MCP de Node).
   - **`creator-cv-gemini`**: herramienta **`gemini_generate`** (modelo por defecto `gemini-2.0-flash`, configurable con `GEMINI_MODEL`).
5. En el chat, pide a la IA que use esa carpeta como **fuente de verdad** y que actualice `cv-context.active.json` / `cv-interview.pending.json` según el flujo.

## Git y privacidad

Si versionas el repo, añade `context/cv-context.active.json` a `.gitignore` cuando contenga datos personales. La plantilla puede quedar en el repo.

## Aplicación web Creator CV (Flask)

La app Flask usa el **mismo archivo** `context/cv-context.active.json` (o el que indiques) para mantener el contexto alineado con el MCP de Cursor:

- Variable de entorno **`CREATOR_CV_CONTEXT_PATH`**: ruta absoluta al JSON activo. Si no está definida, se usa por defecto `mcp-ia-preguntas/context/cv-context.active.json` respecto a la raíz del repo.
- En la interfaz: **Importar desde archivo MCP** copia el archivo al CV en base de datos; **Exportar al archivo MCP** escribe el JSON del CV al disco (Cursor lo verá en la siguiente lectura vía MCP).
- **Entrevista MCP** (`/cvs/<id>/interview/mcp`): la IA escribe `cv-interview.pending.json`; la app muestra `question_markdown` como HTML, guarda la respuesta en el contexto y suma texto a la revisión en BD y en `context/cv-review-cv<id>.active.md`. Variables opcionales: `CREATOR_CV_INTERVIEW_PENDING_PATH`, `CREATOR_CV_REVIEW_PATH` (puedes usar el marcador `{id}` para separar por CV).
- Desarrollo: `uv run flask --app creator_cv:create_app run` y abre la raíz `/`.

## Sugerencia de modelo

- **Para este flujo** (muchas preguntas cortas, JSON estructurado, español/inglés, sin alucinar datos): usa el modelo **más capaz** que tengas disponible en Cursor en conversaciones donde importe la precisión (p. ej. Sonnet / Opus, GPT‑4.1 u otra variante “pro” del día: nombres exactos cambian según el producto).
- **Para iteraciones muy largas** solo de borrador, puedes usar un modelo rápido en las primeras rondas y **cambiar a uno más fuerte** para la pasada final (JSON + Markdown del CV).
- Criterio práctico: si ves omisiones en fechas, mezcla de idiomas o JSON mal cerrado, sube de tier de modelo antes de tocar el esquema.
