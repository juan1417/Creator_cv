---
name: flask
description: Diseña, implementa y depura aplicaciones web con Flask, incluyendo rutas, vistas, plantillas Jinja, formularios (Flask-WTF) y persistencia con SQLAlchemy. Use when el usuario menciona `Flask`/`flask`, muestra código `.py` con `app = Flask(...)`, `Blueprint`, `render_template`, `FlaskForm`, `SQLAlchemy` o pide ayuda con errores comunes de Flask.
---

# Flask (Web App Helper)

## Objetivo
Ayudar a construir y corregir features de una app Flask de punta a punta (rutas + lógica + persistencia + templates/formularios + pruebas básicas), respetando el estilo y estructura del proyecto existente.

## Cuando aplicar esta skill
1. El usuario menciona `Flask`/`flask` o un patrón tipo `app = Flask(...)`.
2. El contexto incluye archivos `.py` que usan `Blueprint`, `render_template`, `FlaskForm` o `SQLAlchemy`.
3. El usuario reporta errores típicos (404 por rutas/blueprints, `CSRF token missing`, configuración de BD, import/circular imports, etc.).

## Información mínima a pedir si no está clara
- Nombre y rol del/los archivos de entrada (por ejemplo `app.py`, `wsgi.py`, `manage.py`).
- Patrón usado: `app = Flask(...)` directo o `create_app()` factory.
- Extensiones ya existentes (por ejemplo `db`, `migrate`, `csrf`, `login_manager`).
- Estructura de carpetas (por ejemplo `templates/`, `static/`, `blueprints/`).
- Base de datos (SQLite/Postgres/etc.) y cómo se configuran las variables (env o config object).

Si falta alguno de esos puntos y es relevante para la solución, preguntar antes de proponer código final.

## Flujo guiado
1. **Diagnóstico rápido del estado actual**
   - Identificar si hay factory (`create_app`) o app global.
   - Detectar blueprints existentes y prefijos (`url_prefix`).
   - Identificar cómo se configura DB y migraciones (si aplica).
   - Localizar el flujo de templates (Jinja) y formularios (si usa Flask-WTF).
2. **Definir el objetivo exacto**
   - ¿Es una ruta nueva? ¿un endpoint? ¿una vista con template?
   - ¿Necesita formulario y validación? ¿necesita persistencia en SQLAlchemy?
3. **Diseñar el contrato**
   - Métodos (`GET/POST/PUT/DELETE`), URLs y status codes esperados.
   - Campos esperados (query params, form fields, JSON) y validaciones.
4. **Implementar por capas (en orden)**
   - **Extensiones/Config**: reutilizar o inicializar `db`, `migrate`, `csrf`, etc.
   - **Rutas/Blueprints**: crear o actualizar rutas con manejo de errores.
   - **Lógica**: escribir la función que procesa la solicitud (validación + side effects).
   - **Modelos (SQLAlchemy)**: agregar/actualizar modelos y relaciones cuando sea necesario.
   - **Templates (Jinja)**: crear/actualizar vistas con `url_for` y contexto consistente.
   - **Formularios (Flask-WTF)**: definir `FlaskForm`, validaciones y render del CSRF.
5. **Conectar y ejecutar**
   - Asegurar que el blueprint está registrado en el sitio correcto.
   - Indicar cómo levantar la app (`flask run` o comando equivalente del proyecto).
6. **Pruebas y verificación manual**
   - Comprobar navegación (GET) y envío (POST) con un ejemplo mínimo.
   - Verificar mensajes de validación (formularios) y errores DB (si aplica).
7. **Revisión de seguridad y calidad**
   - CSRF activado cuando haya Flask-WTF.
   - Inputs validados antes de persistir.
   - Evitar inyección en queries (uso de ORM/parametrización).

## Reglas de implementación
- Si el proyecto usa el patrón `create_app()`, respetar el factory y no crear una segunda app global.
- Si ya existen objetos de extensiones (`db = SQLAlchemy()`, `csrf = CSRFProtect()`), reutilizarlos en lugar de recrearlos.
- No inventar estructura del proyecto: si no se ve `templates/`, preguntar o ajustar el plan a lo que exista.
- Cuando haya cambios en modelos con SQLAlchemy, proponer migraciones y comentar el comando típico (sin asumir nombres si no se ven).

## Formato de salida recomendado (steps + snippets)
1. **Resumen de cambios** en 3-6 bullets.
2. **Pasos concretos** numerados.
3. **Snippets** organizados por sección:
   - `Blueprint / Route`
   - `Model (SQLAlchemy)`
   - `Form (Flask-WTF)`
   - `Template (Jinja)`
   - `Config / Extensions`
4. **Cómo probar** con 1-3 comandos o acciones manuales.

## Checklist rápido por feature
### Rutas / vistas
- [ ] URL final correcta (prefijo de blueprint + ruta)
- [ ] Manejo de 400/404 con mensajes útiles
- [ ] Uso consistente de `url_for`

### Templates (Jinja)
- [ ] Variables del template coinciden con el contexto enviado
- [ ] Formularios con `method` correcto y campos esperados

### Formularios (Flask-WTF)
- [ ] CSRF token presente (`{{ form.csrf_token }}` o equivalente)
- [ ] Validación y feedback al usuario

### SQLAlchemy
- [ ] Modelos con campos y relaciones coherentes
- [ ] Persistencia solo después de validación

## Ejemplos
### Ejemplo 1: error CSRF en formulario
Input del usuario: “Me sale `The CSRF token is missing` cuando envío el formulario”.
Salida esperada: pasos para ubicar inicialización de `CSRFProtect`, añadir/render de `csrf_token` en el template, y asegurar que el formulario usa `FlaskForm`.

### Ejemplo 2: crear una vista con blueprint + template
Input del usuario: “Quiero una ruta `/clientes` con listado en HTML”.
Salida esperada: blueprint con ruta `GET`, consulta SQLAlchemy (si aplica), render `render_template`, y cómo registrar el blueprint en el app factory.

### Ejemplo 3: implementar endpoint REST simple
Input del usuario: “Necesito un endpoint `POST /api/items`”.
Salida esperada: validación de entrada (form o JSON según el caso), persistencia con SQLAlchemy, y respuesta con status code y payload.
