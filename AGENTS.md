# Creator_cv — OpenCode / AI agent instructions

Flask 3.x web app for creating, editing, and exporting CVs from JSON context. Spanish-first UI, MCP servers for Cursor integration.

## Quick reference

```bash
uv sync                    # install all deps
uv sync --group mcp        # install MCP deps (fastmcp)
uv run flask --app creator_cv:create_app run          # dev server (port 5000)
uv run pytest                                        # run tests (none exist yet)
uv run python -m creator_cv.seed_prueba              # insert demo CV (fictitious data)
```

## Architecture

- **App factory**: `creator_cv/__init__.py:create_app()`
- **Single blueprint**: `creator_cv/blueprints/main.py` — all routes in one file (~630 lines)
- **Single user**: `dev@local` (no auth; email is the default user identifier)
- **DB**: SQLAlchemy + Flask-Migrate (Alembic). Default: `sqlite:///creator_cv.sqlite3`. Override via `DATABASE_URL`.
- **CSRF**: global via Flask-WTF `CSRFProtect`. Disabled for `/interview/mcp` endpoint.
- **Cache**: aggressive `no-store` on all non-static HTML responses (dev convenience)
- **Gemini**: uses `google-genai` client; loaded from `.env` at repo root. Keys: `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_MODEL_FALLBACKS` (comma-separated, tried on 429).

## MCP servers (Cursor/stdio)

Two FastMCP servers in `creator_cv/mcp/`:

| Tool | Run command |
|------|------------|
| Context filesystem | `uv run --group mcp python -m creator_cv.mcp.fs_server <absolute-context-dir>` |
| Gemini generation | `uv run --group mcp python -m creator_cv.mcp.gemini_server` |

MCP + web app share context via JSON files on disk. See `mcp-ia-preguntas/CONEXION-CURSOR.md`.

## Key conventions

- **No invented data**: never fabricate CV dates, roles, companies, metrics. Leave explicit placeholders.
- **Spanish by default**: UI copy, prompts, and codebase docs are in Spanish. Reply in the user's language.
- **uv only**: no pip, no requirements.txt. `pyproject.toml` + `uv.lock` are the source of truth. Never edit `uv.lock` manually.
- **Python 3.14** (`.python-version`)
- **No linter / formatter / typechecker** configured. No CI.
- **No tests exist** yet (pytest is a dev dependency but no test files found).
- **Export formats**: PDF (fpdf2 or WeasyPrint), DOCX (python-docx), Markdown.
- Playwright is a dependency (may be needed for PDF rendering).

## File system context files

```
mcp-ia-preguntas/context/
  cv-context.active.json          # shared context (web + MCP)
  cv-context.template.json        # empty template
  cv-interview.cv{id}.pending.json  # per-CV interview question
  cv-review-cv{id}.active.md      # per-CV review markdown
```

Paths configurable via `CREATOR_CV_CONTEXT_PATH`, `CREATOR_CV_INTERVIEW_PENDING_PATH`, `CREATOR_CV_REVIEW_PATH`.
