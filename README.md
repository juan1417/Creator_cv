# Creator CV (versión estática · localStorage)

Crea, edita y descarga CVs. **Frontend puro** (HTML + JS + CSS) — sin servidor,
sin base de datos. Los CVs viven en `localStorage` del navegador.

Reemplazo 1-a-1 de la versión Flask + SQLite anterior, con la misma UI y los
mismos flujos. Desplegable en **Vercel** (hosting estático) en un click.

## Características

- Crear / editar / eliminar CVs
- Editor de JSON con validación en vivo
- Asistente guiado (formulario paso a paso)
- Chat con Gemini (vía Vercel serverless function)
- Vista previa tipo Harvard de una columna
- Exportar a PDF (jsPDF en cliente) y Markdown
- Compatibilidad con oferta (cruce de términos, client-side)
- Export / import de todo el `localStorage` a JSON (para backup o migración entre navegadores)

## Estructura

```
.
├── index.html             # Lista de CVs + crear + export/import
├── cv-edit.html           # Editor JSON con toolbar
├── cv-preview.html        # Vista previa (hoja A4)
├── cv-interview.html      # Asistente guiado
├── cv-chat.html           # Chat con Gemini
├── cv-job-fit.html        # Compatibilidad con oferta
├── api/
│   └── gemini.js          # Vercel function: proxy a Gemini
├── assets/
│   ├── css/app.css        # Design system Dovetail (mismo que la versión Flask)
│   └── js/                # storage, cv-store, render, pdf, chat, etc.
├── vercel.json            # Routing + headers + cache
├── package.json
└── scripts/
    └── export_to_json.py  # Migra los CVs de la versión Flask → JSON importable
```

## Deploy en Vercel

### 1) Conectar el repo

1. Subí este directorio a un repo de GitHub.
2. Andá a [vercel.com/new](https://vercel.com/new) y elegí el repo.
3. Vercel detecta el sitio estático automáticamente. **No hace falta build command**.

### 2) Configurar Gemini (opcional, solo si usás el chat)

Si vas a usar el chat con IA, configurá la API key como variable de entorno en Vercel:

- Settings → Environment Variables
- Nombre: `GEMINI_API_KEY`
- Valor: tu key de [aistudio.google.com](https://aistudio.google.com/app/apikey)
- Environments: Production (y Preview si querés)

Modelo por defecto: `gemini-2.5-flash` (override con `GEMINI_MODEL`). Fallbacks editables con `GEMINI_MODEL_FALLBACKS` (CSV).

### 3) Deploy

Click **Deploy**. Tu sitio queda en `https://<nombre>.vercel.app`.

Cada push a `main` redeploy automático. Cada PR crea un preview.

## Migrar CVs de la versión Flask

Si tenés CVs en la base de datos SQLite de la versión anterior:

```bash
# Desde la raíz del proyecto antiguo (con el venv de Flask activo):
uv run python scripts/export_to_json.py --output export-cvs.json
```

Eso te genera un `export-cvs.json` con todos los CVs. En la app nueva:

1. Abrí la página principal (`/`)
2. Click en **Importar (.json)**
3. Elegí el `export-cvs.json`
4. Confirmá la importación

Los CVs se crean como nuevos (no se duplican si ya tenés uno con el mismo título).

## Backup entre navegadores / dispositivos

En la página principal, sección **Respaldo**:

- **Exportar todo (.json)** → descarga un JSON con todos los CVs, chats y config
- **Importar (.json)** → carga ese JSON (reemplaza lo local)

> ⚠️ `localStorage` se borra si el usuario limpia datos del navegador. Hacé
> backup periódicamente, o exportá cuando cambies de navegador/dispositivo.

## Desarrollo local

No necesitás servidor: abrí `index.html` directamente en el navegador. Pero
algunos navegadores bloquean `fetch` y otras cosas con `file://`. Mejor:

```bash
# Cualquier servidor estático:
python3 -m http.server 8000
# o
npx serve .
# o
uv run python -m http.server 8000
```

Y abrí `http://localhost:8000`.

## Cambios respecto a la versión Flask

| Antes (Flask) | Ahora (estático) |
|---|---|
| SQLite en `instance/creator_cv.sqlite3` | `localStorage` del navegador |
| Autenticación CSRF | No aplica |
| PDF con fpdf2 (servidor) | PDF con jsPDF (cliente) |
| DOCX con python-docx | DOCX básico como `.doc` (Word lo abre). Para `.docx` real se necesita backend o jszip+docxtemplater. |
| MCP servers para Cursor | No aplica (MCP requiere backend) |
| Chat con Gemini server-side | Chat con Gemini vía `/api/gemini` (Vercel function) |
| Asistente local en Python | Asistente local en JS (mismo flujo) |
| Alembic migrations | No aplica (datos locales) |

## Limitaciones

- `localStorage` ≈ 5–10 MB por origen. Suficiente para muchos CVs, pero no infinito.
- Los datos NO se sincronizan entre dispositivos. Usá export/import para mover.
- El PDF se genera en el cliente (jsPDF), no en servidor. La tipografía puede
  variar respecto a la versión anterior (que usaba fpdf2 + Arial del sistema).
- DOCX se exporta como `.doc` (HTML con cabecera Word). Para `.docx` real
  hace falta una lib adicional (ej. `jszip` + `docxtemplater`).

## Licencia

MIT
