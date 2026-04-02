---
name: python-uv
description: Gestiona entornos y dependencias Python con uv (inicialización de proyecto, pyproject.toml, lockfile, sincronización y ejecución de comandos). Usar cuando el usuario mencione uv, Astral uv, sustituto o alternativa a pip o poetry, pyproject.toml, uv.lock, venv rápido, instalar paquetes Python o ejecutar scripts con uv run.
---

# Python con uv

## Objetivo

Priorizar **uv** como herramienta por defecto para **dependencias, entornos y ejecución** en proyectos Python de este workspace (p. ej. una futura app Flask), salvo que el repo ya imponga otra herramienta de forma explícita (solo Poetry, solo pip-tools, etc.).

## Cuándo aplicar

1. El usuario pide añadir, actualizar o documentar dependencias Python.
2. Aparece o se propone `pyproject.toml` / `uv.lock`.
3. El usuario menciona `uv`, “Astral”, “más rápido que pip” o migración desde pip/poetry.
4. Hay que reproducir un entorno o correr tests/comandos en un venv consistente.

## Flujo recomendado

### Proyecto nuevo

1. En la raíz del paquete/app: `uv init` (si aún no hay proyecto definido).
2. Crear entorno: `uv venv` (por defecto `.venv` en el directorio actual).
3. Activar el venv según el shell del usuario (Windows PowerShell: `.venv\Scripts\Activate.ps1`).
4. Añadir dependencias: `uv add nombre-paquete` (runtime) o `uv add --dev nombre-paquete` (desarrollo).
5. Instalar según lock: `uv sync`.
6. Ejecutar sin activar manualmente cuando convenga: `uv run python …`, `uv run pytest`, `uv run flask …`, etc.

### Proyecto existente con `pyproject.toml` + `uv.lock`

1. `uv sync` para alinear el entorno con el lock.
2. Cambios de dependencias con `uv add` / `uv remove`; commitear `pyproject.toml` y `uv.lock` cuando el flujo del equipo lo exija.

### Solo hay `requirements.txt` (legacy)

1. Opción preferida a medio plazo: migrar a `uv init` + `uv add` equivalente, o importar según documentación actual de uv para ese caso.
2. Si el usuario pide no migrar aún, respetar `requirements.txt` y no forzar uv salvo que pida instalar uv o unificar tooling.

## Comandos de referencia (memoria rápida)

| Necesidad | Comando típico |
|-----------|------------------|
| Sincronizar deps | `uv sync` |
| Añadir paquete | `uv add paquete` |
| Añadir dev | `uv add --dev paquete` |
| Quitar paquete | `uv remove paquete` |
| Actualizar lock | `uv lock` (cuando aplique tras cambios manuales acordados) |
| Ejecutar algo en el proyecto | `uv run …` |

Ajustar flags exactos a la versión de uv instalada si el usuario reporta diferencias en la CLI.

## Coexistencia con Flask

- Al usar el skill **flask**, instalar `flask` (y extensiones) con **`uv add`**; ejecutar la app con **`uv run`** para reducir “funciona en mi máquina” por PATH incorrecto.
- No mezclar en el mismo mensaje instrucciones contradictorias (p. ej. `pip install -r` y `uv sync`) sin dejar claro cuál es la fuente de verdad del proyecto.

## Buenas prácticas

- Tratar **`uv.lock`** como artefacto compartido cuando el equipo ya lo versiona; no editarlo a mano.
- Documentar en README solo **una** vía de instalación principal (idealmente uv).
- En CI, preferir `uv sync` + `uv run` para comprobar que el lock es reproducible.
