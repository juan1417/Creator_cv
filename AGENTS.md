# Creator_cv — OpenCode / AI agent instructions

Plataforma para crear, editar y exportar CVs desde un contexto JSON. Backend
Flask con Clean Architecture sobre Postgres (Neon). Frontend React + Vite + TS.

## Estructura real del repo

```
.
├── backend/        # Flask 3.x + SQLAlchemy 2.x + Alembic + Neon/Postgres
│   ├── src/
│   │   ├── domain/          # entidades, contratos de repo, excepciones
│   │   ├── application/     # use cases, DTOs (Pydantic)
│   │   ├── infrastructure/  # SQLAlchemy, Flask, auth JWT
│   │   ├── composition/     # app factory (composition root)
│   │   └── main.py
│   ├── alembic/             # migraciones
│   ├── tests/               # pytest (use cases con repos en memoria)
│   ├── docs/                # README detallado
│   └── pyproject.toml
└── frontend/       # React 18 + Vite + TypeScript + react-router-dom
    ├── src/
    │   ├── pages/           # Home, Login, Editor, Preview
    │   ├── components/
    │   └── lib/             # api.ts, auth-context.tsx
    ├── package.json
    └── vite.config.ts
```

> ⚠️ El repo no tiene un paquete `creator_cv/` en la raíz — el código vive
> en `backend/`. Esta nota la aclaro porque distintos agents/READMEs viejos
> pueden seguir describiendo el layout anterior.

## Quick reference

```bash
# Backend
cd backend
uv sync                              # instalar deps
uv run alembic upgrade head          # crear/actualizar tablas en Neon
uv run python -m src.main            # arrancar API en :8000
uv run pytest                        # tests (repos en memoria, no tocan DB)

# Frontend
cd frontend
npm install
npm run dev                          # Vite dev server en :5173
```

## Variables de entorno requeridas

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | Postgres/Neon connection string |
| `JWT_SECRET_KEY` | Secreto HMAC para firmar access/refresh JWTs (HS256) |
| `ENCRYPTION_KEY` | Clave Fernet (base64 32 bytes) para encriptar secrets 2FA TOTP |

## Arquitectura

- **App factory**: `backend/src/composition/app_factory.py:build_app()`
- **Rutas**: `backend/src/infrastructure/web/routes.py` (Blueprint `/api`)
- **Capas**: `domain` (reglas puras) → `application` (use cases, DTOs) →
  `infrastructure` (Flask, SQLAlchemy, JWT) → `composition` (DI).
- **Auth**: JWT HS256 + refresh tokens opacos con rotación. Access token 15 min,
  refresh token 30 d con detección de robo por familia.
  El cliente guarda ambos en `localStorage` y refresca automáticamente.
- **2FA**: TOTP (RFC 6238) con secretos encriptados vía Fernet. 10 backup codes
  por usuario, hasheados en DB, mostrados una sola vez en setup.
- **DB**: SQLAlchemy 2.x sobre Postgres/Neon. Driver `psycopg` v3, SSL
  automático, `pool_pre_ping` para tolerar auto-suspend de Neon.
  Schemas versionados con Alembic (NO se usa `create_all` en Postgres).
- **CSRF**: no aplica — la API usa JWT en header, no cookies de sesión.
- **Rate limiting**: Flask-Limiter con storage Postgres propio (`limits` v5 no
  tiene backend Postgres nativo). 5 intentos/hora en register, 10/15min en login.
- **Frontend dashboard**: cards con thumbnail auto-scalado, search, sort, filter,
  templates al crear CV.
- **Editor**: split-pane con formularios estructurados (7 secciones) + preview
  en vivo + autosave con debounce.
- **PDF export**: html2canvas + jsPDF (lazy import) — captura el paper A4 y lo
  descarga como PDF.

## MCP servers (Cursor/stdio)

Dos servidores FastMCP en `backend/src/creator_cv/mcp/` (legacy) — ver
`mcp-ia-preguntas/CONEXION-CURSOR.md` si están activos en tu setup.

## Convenciones clave

- **No inventar datos**: nunca fabricar fechas, roles, empresas o métricas
  para un CV. Dejar placeholders explícitos.
- **Español por defecto**: copy de UI, prompts, mensajes de error y docs.
- **uv only**: nada de pip ni `requirements.txt`. `uv.lock` es la fuente
  de verdad. Nunca editar `uv.lock` a mano.
- **Python 3.12+** (`.python-version`, `pyproject.toml`).
- **No linter / formatter / typechecker** configurado a nivel repo (Ruff está
  en `pyproject.toml` pero no se corre automáticamente). Sin CI todavía.
- **Tests**: existen tests unitarios de use cases con repos en memoria.
  No hay tests de integración contra DB real todavía.
- **Export formats** (futuro): PDF (fpdf2 o WeasyPrint), DOCX (python-docx),
  Markdown.

## Setup con Neon (primera vez)

1. `npx neonctl@latest init` desde la raíz → crea branch + connection string.
2. Copiar URL a `backend/.env` como `DATABASE_URL=postgresql://...`.
3. `cd backend && uv sync && uv run alembic upgrade head`.
4. Arrancar con `uv run python -m src.main`. El log debe decir
   `DB: Postgres → postgresql+psycopg://...@...`.

> ⚠️ **Seguridad**: nunca commitear `DATABASE_URL` con credenciales reales.
> `.env` ya está en `.gitignore`. Si una credencial queda expuesta en el chat
> o en un commit, rotala en Neon inmediatamente.
