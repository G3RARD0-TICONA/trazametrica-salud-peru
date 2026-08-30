# Trazabilidad y puerta G17

## Requisitos

| Fuente | Evidencia P17 | Verificación |
|---|---|---|
| RNF-001–003 | mínimo privilegio, sesiones, datos sintéticos y escaneo | pruebas y puertas de seguridad |
| RNF-004–005 | rollback, inmutabilidad y determinismo heredados | regresión P06–P16 |
| RNF-006–007 | p95, consultas, 100 000 observaciones y XLSX 10 000 | pruebas marcadas `performance` |
| RNF-008 | estructura y checklist WCAG 2.2 AA | auditor automático y revisión manual |
| RNF-009–012 | configuración, cobertura, correlación y zona horaria | CI, middleware y pruebas |
| RNF-013 | manifiesto antes/después de restauración | comando y prueba de divergencia |

## Controles G17

| N.° | Control | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance transversal trazado | RNF-001–013 y límites P18 | Conforme |
| 2 | Regresión funcional | suite P06–P16 conservada | Conforme |
| 3 | Seguridad de aplicación | Argon2, sesiones, CSRF, permisos y cabeceras | Conforme |
| 4 | Repositorio seguro | secretos, datos reales y artefactos prohibidos | Conforme |
| 5 | Integridad y recuperación | manifiesto reproducible y divergencia detectable | Conforme |
| 6 | Rendimiento ordinario | p95 ≤2 s y ≤20 consultas | Conforme |
| 7 | Importación de referencia | 10 000 filas ≤60 s | Conforme |
| 8 | Accesibilidad | auditor estructural y checklist WCAG 2.2 AA | Conforme |
| 9 | Observabilidad segura | correlación y denegaciones sin entrada sensible | Conforme |
| 10 | Documentación y límites | expediente P17 y exclusiones productivas | Conforme |
| 11 | CI oficial PostgreSQL 17 | pruebas, cobertura, deploy check, seguridad, dependencias e imagen | Pendiente |
| 12 | Aceptación formal del titular | autorización explícita de cierre e integración | Pendiente |

**Resultado previo a CI:** 10/12 controles conformes. G17 permanece abierta y el PR debe permanecer en borrador.
