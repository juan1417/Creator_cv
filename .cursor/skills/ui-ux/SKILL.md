---
name: ui-ux
description: Aplica principios de interfaz y experiencia de usuario al diseñar o revisar pantallas, flujos y componentes web. Cubre jerarquía visual, espaciado, tipografía, color, estados de interacción, accesibilidad y coherencia con el sistema existente. Usar cuando el usuario mencione UI, UX, interfaz, diseño de pantallas, usabilidad, accesibilidad (a11y), mockups, wireframes o pulir la experiencia de una app o sitio.
---

# UI/UX

## Objetivo

Priorizar **claridad, previsibilidad y accesibilidad** en cada cambio de interfaz. El resultado debe sentirse coherente con el resto del proyecto (patrones, tokens, componentes ya usados).

## Cuándo aplicarlo

- Nuevas pantallas, formularios, dashboards o navegación.
- Refinos visuales: espaciado, tipografía, color, alineación.
- Revisiones de usabilidad o de accesibilidad.
- Flujos con muchos pasos o estados de error/carga/vacío.

## Principios rápidos

1. **Jerarquía**: una acción principal por vista o sección; títulos y CTAs claramente diferenciados.
2. **Consistencia**: reutilizar componentes y convenciones del proyecto antes de inventar variantes.
3. **Feedback**: estados hover, focus, active, disabled, loading y error visibles y comprensibles.
4. **Escaneo**: alineación en rejilla, agrupación por proximidad, listas y etiquetas explícitas.
5. **Accesibilidad**: contraste suficiente, foco visible, orden lógico del teclado, textos alternativos donde corresponda, `aria-*` cuando el patrón lo requiera.
6. **Responsive**: contenido usable en anchos estrechos; evitar depender solo del hover para información crítica.

## Checklist antes de dar por cerrada una UI

- [ ] ¿El usuario entiende qué puede hacer en los primeros segundos?
- [ ] ¿Hay una jerarquía clara (título → contenido → acción)?
- [ ] ¿Los errores indican qué falló y cómo corregirlo?
- [ ] ¿Los campos obligatorios y los formatos esperados están claros?
- [ ] ¿Focus y lectores de pantalla tienen un orden coherente?
- [ ] ¿Estados vacíos y de carga tienen mensaje o esqueleto útil?

## Implementación en código

- **Espaciado**: escala consistente (p. ej. múltiplos de 4 u 8 px) según lo que ya use el proyecto.
- **Tipografía**: pocas familias y tamaños; line-height legible en párrafos largos.
- **Color**: no basar solo el color para transmitir estado; combinar con icono o texto.
- **Formularios**: etiquetas asociadas a inputs, mensajes de error junto al campo afectado.
- **Interacción**: targets táctiles razonables; evitar zonas de clic demasiado pequeñas.

## Revisión de UI (formato sugerido)

Al revisar cambios de interfaz, estructurar el feedback así:

- **Crítico**: bloquea comprensión, accesibilidad grave o inconsistencia que rompe el flujo.
- **Mejora**: jerarquía, espaciado, copys, microinteracciones.
- **Opcional**: refinamientos estéticos sin impacto en tareas principales.

Mantener el feedback **accionable** (qué cambiar y dónde), alineado con los patrones ya presentes en el repositorio.
