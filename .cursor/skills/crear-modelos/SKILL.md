---
name: crear-modelos
description: Diseña e implementa modelos de datos con SQLAlchemy (Flask-SQLAlchemy): entidades, campos, relaciones, restricciones e índices, y coordina migraciones. Use when the user asks to crear modelos, entidades ORM, tablas SQLAlchemy, relaciones 1-N/N-N, esquema de base de datos, o al editar modelos .py con `db.Model` / declarative.
---

# Crear modelos (datos / ORM)

## Alcance

Este skill cubre **modelos de persistencia** (ORM / tablas). Si el usuario quiere **modelos de machine learning**, pedir confirmación y no aplicar estas reglas de SQLAlchemy.

## Cuándo aplicar

1. Pide crear o cambiar **modelos**, **entidades**, **tablas** o **esquema relacional**.
2. Aparece código con `db.Model`, `Mapped`, `relationship`, `ForeignKey`, `SQLAlchemy`, Flask-SQLAlchemy o Alembic.
3. Necesita definir **PK**, **FK**, **unique**, **índices** o **relaciones** (1-1, 1-N, N-N).

## Coordinación con otras skills

- Si el flujo es una feature Flask completa (rutas + templates + forms), combinar con la skill `flask` y usar esta skill para la capa de modelo.

## Información mínima antes de codificar

Si falta, preguntar solo lo necesario:

- Motor de BD (SQLite, Postgres, MySQL, etc.) y si ya existe `db` / factory.
- Nombres de entidades y cardinalidad esperada entre ellas.
- Campos obligatorios vs opcionales; unicidad; borrado (soft delete o hard delete).
- Si el proyecto ya usa **Alembic** / Flask-Migrate y convención de revisiones.

## Flujo de trabajo

1. **Inventario del dominio**: lista de entidades y relaciones en texto corto.
2. **Contrato de datos**: por entidad, columnas + tipos + nullability + defaults + constraints.
3. **Diseño de relaciones**:
   - 1-N: FK en el lado "muchos"; `back_populates` o `backref` según estilo del proyecto.
   - N-N: tabla asociación explícita o `secondary=` si el proyecto ya lo usa.
4. **Implementación** siguiendo el estilo existente:
   - Misma convención de nombres (`snake_case` tablas/columnas si así está el repo).
   - Timestamps (`created_at` / `updated_at`) solo si el proyecto los usa o el usuario los pide.
5. **Índices**: proponer índices para FKs frecuentes y búsquedas declaradas por el usuario.
6. **Migración**: indicar que hay que generar/aplicar migración cuando cambie el esquema; no afirmar nombres de comandos si no están en el repo — inferirlos o preguntar.

## Reglas de calidad

- No inventar columnas o relaciones no confirmadas.
- Evitar imports circulares: `TYPE_CHECKING` o imports diferidos si el patrón del proyecto lo requiere.
- Strings con longitud razonable (`String(255)` etc.) salvo que el usuario defina otro contrato.
- Passwords y secretos: nunca en texto plano; si el usuario pide "campo password", asumir hash (bcrypt/argon2) según stack del proyecto.
- **Integridad**: `ondelete` coherente con reglas de negocio cuando use FKs.

## Plantilla mental (ajustar a SQLAlchemy 1.x/2.x del proyecto)

- Modelo = clase + `__tablename__`.
- PK explícita (`id` entero autoincrement o UUID si el proyecto usa ese patrón).
- FKs con índice implícito o explícito según necesidad de queries.

## Formato de salida recomendado

1. Resumen del modelo (entidades y relaciones) en 3-8 bullets.
2. Código propuesto en el estilo del repositorio.
3. Notas de migración (qué revisar en Alembic / riesgos).
4. Checks rápidos: constraints, índices, cascadas, datos existentes si la tabla ya tiene filas.

## Cierre

Validar antes de entregar:

- [ ] Nombres alineados con el resto del proyecto
- [ ] Relaciones bidireccionales consistentes (`back_populates` sin duplicar nombres)
- [ ] Nullable/default correctos para campos obligatorios
- [ ] Plan de migración mencionado cuando el cambio es persistente
