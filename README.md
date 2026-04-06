# Creator CV

Aplicación web en Flask para crear, editar y exportar currículums desde un contexto JSON. Incluye vista previa moderna, exportación a PDF/DOCX/Markdown, entrevista guiada (local y MCP) y herramientas de apoyo con IA.

## Paso a paso: instalación y uso

1. **Clona el repositorio**
   ```bash
   git clone <URL_DEL_REPO>
   cd Creator_cv
   ```

2. **Instala dependencias con uv**
   ```bash
   uv sync
   ```

3. **(Opcional) Instala dependencias MCP**
   ```bash
   uv sync --group mcp
   ```

4. **Configura variables de entorno**
   - Copia `.env.example` a `.env`.
   - Completa al menos:
     - `GEMINI_API_KEY` (si usarás funciones de IA)
     - `GEMINI_MODEL` (opcional)
     - `GEMINI_MODEL_FALLBACKS` (opcional)

5. **Levanta la aplicación**
   ```bash
   uv run flask --app creator_cv:create_app run
   ```

6. **Abre la app**
   - Navega a: `http://127.0.0.1:5000`

7. **Crea y edita un CV**
   - Desde inicio crea un CV nuevo.
   - En el editor JSON guarda cambios.
   - Usa **Vista previa** para validar diseño.

8. **Exporta tu CV**
   - Desde el editor puedes descargar:
     - `.md`
     - `.pdf`
     - `.docx`

9. **(Opcional) Flujo MCP con Cursor**
   - Revisa `mcp-ia-preguntas/CONEXION-CURSOR.md`.
   - Sirve para sincronizar contexto, preguntas pendientes por CV y revisión markdown.

## Comandos útiles

- Ejecutar servidor:
  ```bash
  uv run flask --app creator_cv:create_app run
  ```
- Ejecutar tests (si aplica):
  ```bash
  uv run pytest
  ```

## Notas

- El archivo `.env` no se versiona.
- Si el PDF parece no actualizarse, cierra el visor y vuelve a abrir el archivo exportado.
