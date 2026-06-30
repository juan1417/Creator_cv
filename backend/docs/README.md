# Creator CV — Backend

Stack: Flask 3.x + SQLAlchemy 2.x + Clean Architecture (Hexagonal) + Postgres/Neon.

## Capas

```
src/
  domain/         # entidades, value objects, excepciones, contratos de repo
  application/    # use cases, DTOs (Pydantic), inputs
  infrastructure/ # persistencia (SQLAlchemy), web (Flask), auth (JWT)
  composition/    # app factory (composition root)
  main.py         # entrypoint
```

## Requisitos

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) como gestor de paquetes (único, no pip)
- Para Neon: nada extra, el driver `psycopg` ya está en `pyproject.toml`

## Setup local

```bash
cd backend
uv sync                       # instala deps
uv run alembic upgrade head   # crea las tablas en la DB configurada
uv run python -m src.main     # arranca el servidor en :8000
```

Sin `DATABASE_URL` setteada, se usa SQLite local en `backend/data/creator_cv.sqlite3`
(útil solo para pruebas rápidas — los tipos `UUID`/`JSONB` requieren Postgres).

## Setup con Neon

```bash
# 1. Instalar la CLI de Neon (opcional, podés crear el branch desde la web)
npm i -g neonctl
npx neonctl@latest auth     # una sola vez
npx neonctl@latest init     # crea branch + connection string

# 2. Configurar variables
cp .env.example .env
# Editar .env y pegar la DATABASE_URL que imprimió neonctl.
# El backend agrega el driver `psycopg` y sslmode=require automáticamente.

# 3. Instalar deps y aplicar migraciones
uv sync
uv run alembic upgrade head

# 4. Arrancar
uv run python -m src.main
```

> Si rotás la contraseña de Neon, regenerá `DATABASE_URL` y actualizá `.env`.
> Nunca commitear credenciales (`.env` ya está en `.gitignore`).

### Por qué `psycopg[binary]`

Driver v3 con soporte nativo de tipos (UUID, JSONB, timestamptz). Recomendado
por Neon sobre psycopg2. La URL se normaliza automáticamente:
`postgres://...` → `postgresql+psycopg://...`.

### Pool de conexiones

El engine aplica `pool_pre_ping=True` y `pool_recycle=300s` para tolerar que
Neon escale a cero y cierre conexiones inactivas (escenario habitual en
branches de dev).

## Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | URL de la DB (Postgres recomendado, SQLite legacy) | SQLite local |
| `JWT_SECRET_KEY` | Secreto HMAC para firmar access/refresh JWTs (HS256) | (requerido en prod) |
| `ENCRYPTION_KEY` | Clave Fernet (base64 32 bytes) para encriptar secrets 2FA TOTP | (requerido con 2FA) |
| `CORS_ORIGINS` | Lista separada por coma, o `*` | `*` |
| `FLASK_ENV` | `production` activa modo prod | `development` |
| `LOG_LEVEL` | Nivel de logging (`DEBUG`/`INFO`/`WARNING`/`ERROR`) | `INFO` |

## Migraciones (Alembic)

```bash
# aplicar migración
uv run alembic upgrade head

# rollback
uv run alembic downgrade -1

# generar migración nueva después de cambiar modelos
uv run alembic revision --autogenerate -m "descripcion del cambio"
# revisar SIEMPRE el archivo generado en alembic/versions/ antes de aplicar
```

`alembic/env.py` lee `DATABASE_URL` del entorno — no hace falta editar
`alembic.ini`.

## API

### Auth

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST   | `/api/auth/register` | — | Registrar nuevo usuario (rate limit: 5/h) |
| POST   | `/api/auth/login` | — | Iniciar sesión (rate limit: 10/15min) |
| POST   | `/api/auth/refresh` | — | Refrescar access/refresh tokens (rotación) |
| GET    | `/api/auth/me` | sí | Datos del usuario actual |
| POST   | `/api/auth/logout` | sí | Revocar refresh token actual |
| POST   | `/api/auth/verify-email` | — | Verificar email con token |
| POST   | `/api/auth/resend-verification` | — | Reenviar email de verificación |
| POST   | `/api/auth/forgot-password` | — | Solicitar reset de contraseña (3/h) |
| POST   | `/api/auth/reset-password` | — | Resetear contraseña con token |
| POST   | `/api/auth/2fa/setup` | sí | Iniciar setup de TOTP (devuelve QR + manual key) |
| POST   | `/api/auth/2fa/verify-setup` | sí | Confirmar setup con código TOTP (devuelve backup codes) |
| POST   | `/api/auth/2fa/verify` | — | Verificar 2FA durante login (requiere pending_token) |
| POST   | `/api/auth/2fa/disable` | sí | Desactivar 2FA (requiere password + código) |
| POST   | `/api/auth/2fa/backup-codes` | sí | Regenerar backup codes (requiere password) |

### CVs (requieren `Authorization: Bearer <token>`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/api/cvs` | Listar CVs del usuario |
| POST   | `/api/cvs` | Crear nuevo CV |
| GET    | `/api/cvs/<id>` | Obtener CV por ID |
| PUT    | `/api/cvs/<id>` | Actualizar CV (reemplazo) |
| PATCH  | `/api/cvs/<id>` | Actualizar CV (parcial) |
| DELETE | `/api/cvs/<id>` | Eliminar CV |
| POST   | `/api/cvs/<id>/duplicate` | Duplicar CV |

### Chat (requieren auth)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/api/cvs/<id>/chat` | Obtener historial |
| POST   | `/api/cvs/<id>/chat` | Añadir mensaje |
| DELETE | `/api/cvs/<id>/chat` | Limpiar historial |

## Tests

```bash
cd backend
uv run pytest -v
```

Los tests usan repositorios en memoria (`InMemoryCVRepo`, `InMemoryChatRepo`)
y no tocan la base de datos real — son unitarios rápidos para use cases.

## Convenciones

- **No inventar datos**: nunca fabricar fechas, roles, empresas o métricas
  para un CV. Dejar placeholders explícitos.
- **Español por defecto**: copy de UI, prompts, mensajes de error.
- **Python 3.12+** (definido en `pyproject.toml`).
- **uv only**: no usar pip ni `requirements.txt`. `uv.lock` es la fuente de verdad.
- **No editar `uv.lock` a mano**: dejar que `uv` lo regenere.
