---
name: git-recovery
description: Guía uso de Git para commits, ramas, stash, revert y recuperación del estado del código ante errores o cambios indeseados. Use when the user mentions git, commits, branches, undo, revert, recover, deshacer cambios, recuperar la app, o arreglar el repositorio.
---

# Git: cambios seguros y recuperación

## Objetivo

Usar Git de forma ordenada para que cualquier cambio en la app pueda deshacerse o recuperarse sin perder trabajo colaborativo cuando sea posible.

## Cuándo aplicar esta skill

- El usuario pide deshacer algo, volver atrás, recuperar la app o “como estaba antes”.
- Menciona `git`, `commit`, `branch`, `merge`, `revert`, `reset`, `stash`, `checkout`.
- Hay miedo a romper el repo o dudas sobre qué comando usar.

## Antes de cambios grandes (hábito mínimo)

1. Ver estado: `git status` y `git diff` (o diff por archivo).
2. Trabajar en rama nueva si el cambio es arriesgado: `git checkout -b nombre-rama` (o `git switch -c`).
3. Commit pequeño y frecuente con mensaje claro; evitar un solo commit gigante difícil de revertir.
4. Si el proyecto ya tiene remoto y política de `main`/`master` protegida, no reescribir historia en ramas compartidas sin acuerdo.

## Si algo salió mal: elegir camino

### Cambios sin commitear (solo en el working tree)

- Descartar un archivo: `git restore -- path/to/file` (Git moderno) o `git checkout -- path` (legacy).
- Guardar todo y limpiar para cambiar de tarea: `git stash push -m "mensaje"` y luego `git stash pop` o `git stash apply`.

### Último commit local equivocado (aún no compartido o rama solo tuya)

- Deshacer commit manteniendo cambios en staging: `git reset --soft HEAD~1`.
- Deshacer commit y dejar cambios sin staging: `git reset --mixed HEAD~1` (por defecto).
- **Cuidado**: `git reset --hard` borra cambios no commiteados; solo si el usuario confirma que no los necesita.

### Commit ya subido al remoto (historia compartida)

- Preferir **no reescribir** historia en ramas usadas por otros.
- Deshacer el efecto de un commit con un commit nuevo: `git revert <hash>` (uno o rango según necesidad).
- Resolver conflictos si aparecen y volver a commitear.

### Rama equivocada / merge problemático

- Si el merge no se ha pusheado y quieren abortar: `git merge --abort` (durante conflicto) o volver al estado previo según lo que haya hecho Git en el repo (evaluar `git reflog`).

## `reflog` (último recurso útil)

- `git reflog` lista movimientos recientes de `HEAD`; permite recuperar commits “perdidos” tras reset si aún están en el reflog.
- Tras encontrar el hash deseado: crear rama desde ese punto o `git reset --hard` solo si es seguro y la rama no es compartida.

## Formato de ayuda al usuario

1. Preguntar: ¿cambios commiteados o no? ¿ya hicieron `push`? ¿trabajan solos o con equipo en la misma rama?
2. Recomendar el camino más seguro (restore/stash vs revert vs reset).
3. Dar comandos concretos en orden; advertir cuando un comando es destructivo.
4. Si el repo no es Git o no hay commits, decirlo y sugerir `git init` o clonar según el caso.

## Anti-patrones

- `git push --force` a ramas compartidas sin consenso.
- `--hard` sin confirmar que no hay trabajo sin respaldo.
- Mezclar rebase interactivo en ramas ya integradas por otros sin coordinación.

## Referencia rápida

| Situación | Enfoque típico |
|-----------|----------------|
| Solo archivos locales rotos | `git restore` / `git stash` |
| Mal commit, no pusheado | `git reset` (soft/mixed) o nuevo commit corrigiendo |
| Mal commit ya en remoto | `git revert` |
| “Perdí” un commit | `git reflog` + rama o cherry-pick |
