# Accesibilidad WCAG 2.2 AA

## Verificación automática

`scripts/check_accessibility.py` bloquea la CI si detecta:

- un flujo sin encabezado principal;
- encabezados de tabla sin `scope`;
- controles visibles sin etiqueta asociada o nombre accesible;
- `tabindex` positivo;
- CSS o JavaScript en línea incompatible con la CSP;
- ausencia de idioma, viewport, enlace de salto o región principal.

## Revisión manual del código y los flujos primarios

| Criterio | Evidencia | Estado P17 |
|---|---|---|
| Teclado | enlaces, controles y cierre de sesión usan elementos nativos | Conforme |
| Foco visible | contorno de alto contraste y enlace de salto visible al foco | Conforme |
| Estructura | idioma español, títulos, un `h1` y jerarquía semántica | Conforme |
| Formularios | etiquetas visibles, errores conservados y CSRF | Conforme |
| Tablas | encabezados de columna con `scope` y desplazamiento horizontal | Conforme |
| Contraste | texto oscuro, enlaces subrayados y estados sin depender solo del color | Conforme |
| Reflujo | navegación flexible y diseño utilizable a 320 px | Conforme |
| Movimiento | preferencia `prefers-reduced-motion` respetada | Conforme |
| Mensajes | región `aria-live` y errores identificables | Conforme |

La revisión P17 no equivale a certificación WCAG ni sustituye pruebas con usuarios y tecnologías de asistencia. P18 repetirá la comprobación sobre las páginas efectivamente publicadas.
