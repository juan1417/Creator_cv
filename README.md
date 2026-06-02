# Creator CV

Aplicación web en Flask (multi-usuario) para crear y adaptar currículums a ofertas
de trabajo. Rellena un único formulario con tus datos + habilidades + oferta y, si
quieres, deja que **Gemini** (IA de Google) reescriba tu CV y proponga 3-5
sugerencias. Exporta a **PDF (formato Harvard)** o **DOCX** (Word).

## Características

- 🧍 **Multi-usuario** con registro / login (Flask-Login + SQLite).
- 📥 **Importar CV existente** (PDF o DOCX): la IA extrae los datos y los
  vuelca al editor, donde puedes revisarlos y adaptarlos a una oferta.
- 📝 **Un solo formulario** con secciones colapsables (datos, perfil, experiencia,
  educación, habilidades, proyectos, certificaciones, fortalezas, oferta).
- 🤖 **Adaptación con IA opcional** (Gemini 2.5 Flash). Si no configuras
  `GEMINI_API_KEY`, todo funciona menos los botones "Adaptar" e "Importar".
- 📄 **Export PDF** estilo Harvard (una columna, bullet-point, ATS-friendly)
  usando fpdf2 + fuente Unicode DejaVuSans.
- 📝 **Export DOCX** editable para Word / LibreOffice.
- 🖨️ **Print to PDF** desde el navegador con CSS A4.

## Stack

- **Python** ≥ 3.11
- **Flask** 3.x + Flask-SQLAlchemy + Flask-Migrate + Flask-Login + Flask-WTF
- **fpdf2** (PDF) + **python-docx** (DOCX)
- **pydantic** v2 (validación de CV y schema de Gemini)
- **google-genai** (Gemini)
- **uv** como gestor de dependencias

## Requisitos

- [uv](https://docs.astral.sh/uv/) ≥ 0.4
- Python 3.11 – 3.13

## Instalación

```bash
# 1. Clona y entra al proyecto
git clone <url> Creator_cv && cd Creator_cv

# 2. Instala dependencias
uv sync

# 3. (Opcional) Configura la IA
cp .env.example .env
# Edita .env y añade tu GEMINI_API_KEY (https://aistudio.google.com/app/apikey)

# 4. Crea la base de datos SQLite
uv run flask --app app:create_app db upgrade

# 5. Levanta el servidor
uv run flask --app app:create_app run --debug
```

Abre http://127.0.0.1:5000/ y crea una cuenta.

## Uso

Tienes dos formas de empezar:

### A) Importar un CV existente (PDF o DOCX)

1. **Regístrate** en `/auth/register` (email + contraseña).
2. Click **📥 Importar** en el topbar o en el dashboard.
3. Sube tu archivo (`.pdf` o `.docx`, máx. 10 MB).
4. La IA extrae el texto, lo parsea a JSON, y crea un CV nuevo.
5. Revisa y corrige los datos en el editor; luego pega una oferta y pulsa
   **🤖 Adaptar a oferta con IA** para reescribir el CV.

> ⚠️ Los PDFs escaneados (solo imágenes) no funcionan — la app necesita
> texto digital.

### B) Empezar desde cero

1. Click **+ Nuevo CV** en el topbar o en el dashboard.
2. Rellena las secciones: datos personales, perfil, experiencia, educación,
   habilidades, proyectos, certificaciones, fortalezas…
3. Pega la **oferta de trabajo** en el último bloque.
4. Pulsa **Guardar**.
5. (Opcional) Pulsa **🤖 Adaptar a oferta con IA** — la app reescribirá el
   resumen, los bullets de experiencia y reordenará las habilidades según la
   oferta, y mostrará 3-5 sugerencias en el panel lateral.
6. **Vista previa** abre una hoja HTML limpia lista para imprimir a PDF.
7. **PDF** descarga un PDF estilo Harvard (con tildes/ñ correctas).
8. **DOCX** descarga un Word editable.

## Estructura

```
Creator_cv/
├── app.py                        # entrypoint: app = create_app()
├── pyproject.toml
├── .env.example
├── creator_cv/
│   ├── __init__.py               # create_app() factory
│   ├── config.py
│   ├── extensions.py             # db, migrate, csrf, login_manager
│   ├── models.py                 # User, CV
│   ├── schemas.py                # pydantic CVSchema
│   ├── form_parser.py            # parse flat form data → CV dict
│   ├── cv_render.py              # render_pdf (Harvard), render_docx
│   ├── cv_importer.py            # import PDF/DOCX → text → CVSchema (Gemini)
│   ├── gemini_adapter.py         # adapt + review
│   ├── blueprints/
│   │   ├── auth.py               # /auth/{register,login,logout}
│   │   └── main.py               # /, /dashboard, /cv/* (CRUD + export + import + adapt)
│   ├── static/
│   │   ├── css/                  # app.css, cv.css, cv-form.css
│   │   ├── js/app.js             # form dinámico, chips, fetch para IA
│   │   └── fonts/                # DejaVuSans.ttf (Unicode)
│   └── templates/                # Jinja2
├── tests/                        # pytest
│   ├── conftest.py
│   ├── test_parse_form.py
│   ├── test_validate_cv.py
│   └── test_cv_importer.py
└── instance/creator_cv.sqlite3   # BD (gitignored)
```

## Tests

```bash
uv run pytest
```

Cubre:

- `parse_form_to_cv`: parsea formularios planos con notación
  `experiencia[0][empresa]` y `habilidades[tecnicas][]`.
- `validate_cv`: valida y normaliza el dict del CV con pydantic.

## Variables de entorno

Ver [.env.example](.env.example):

| Variable | Obligatoria | Descripción |
|---|---|---|
| `FLASK_SECRET_KEY` | sí (en prod) | Firma de sesiones y CSRF. |
| `DATABASE_URL` | no | Default: `sqlite:///instance/creator_cv.sqlite3`. |
| `GEMINI_API_KEY` | no | Si está vacía, la IA queda deshabilitada. |
| `GEMINI_MODEL` | no | Default: `gemini-2.5-flash`. |
| `FLASK_DEBUG` | no | `1` para modo desarrollo. |

## Notas

- La fuente **DejaVuSans.ttf** se incluye en `creator_cv/static/fonts/`
  (variantes Regular, Bold, Oblique, BoldOblique). Es necesaria para que
  el PDF soporte tildes, ñ y otros caracteres Unicode.
- Los PDF y DOCX se generan **al vuelo** desde la BD — no se cachean en disco.
- El CV se almacena como JSON validado en `cv.context_json` (TEXT). El schema
  pydantic está en `creator_cv/schemas.py`.

## Licencia

MIT
