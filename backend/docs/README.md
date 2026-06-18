# Creator CV — Backend

Stack: Flask + SQLAlchemy + SQLite (dev) / PostgreSQL (prod)

## Requisitos

- Python 3.12+
- `uv` (gestor de paquetes)

## Setup

```bash
cd backend
uv sync                 # instalar dependencias
uv run flask --app src.main:create_app run  # iniciar servidor (puerto 5000)
```

La base de datos SQLite se crea automáticamente en `backend/data/creator_cv.sqlite3` al arrancar.

## Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | URL de la base de datos (SQLite o PostgreSQL) | `sqlite:///data/creator_cv.sqlite3` |
| `JWT_SECRET_KEY` | Clave secreta para firmar tokens JWT | — (requerida en producción) |
| `CORS_ORIGINS` | Orígenes permitidos para CORS | `*` |

Para producción con PostgreSQL:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/creator_cv
JWT_SECRET_KEY=una-clave-segura-aqui
```

## API

### Auth

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/register` | Registrar nuevo usuario |
| POST | `/api/auth/login` | Iniciar sesión |
| GET | `/api/auth/me` | Obtener datos del usuario actual |

### CVs (requieren `Authorization: Bearer <token>`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/cvs` | Listar CVs del usuario |
| POST | `/api/cvs` | Crear nuevo CV |
| GET | `/api/cvs/<id>` | Obtener CV por ID |
| PUT | `/api/cvs/<id>` | Actualizar CV |
| DELETE | `/api/cvs/<id>` | Eliminar CV |

### Chat (requieren `Authorization: Bearer <token>`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/cvs/<id>/chat` | Obtener historial de chat |
| POST | `/api/cvs/<id>/chat` | Añadir mensaje |
| DELETE | `/api/cvs/<id>/chat` | Limpiar historial |

## Tests

```bash
cd backend
uv run python -m pytest tests/ -v
```

## Migración a PostgreSQL

1. Crear base de datos PostgreSQL
2. Configurar `DATABASE_URL=postgresql://...`
3. Las tablas se crean automáticamente al arrancar (SQLAlchemy `create_all`)
4. Para migraciones avanzadas, integrar Alembic
