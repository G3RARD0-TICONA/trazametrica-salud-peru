# Trazabilidad y puerta G14

## Requisitos

| Fuente | Evidencia P14 | Prueba |
|---|---|---|
| RF-033 / CU-20 | riesgo con contexto, causa, evento, consecuencia y responsable | creación, organización y estado |
| RF-034 | evaluación y control versionados | sustitución, inmutabilidad y aprobación independiente |
| RF-035 | relaciones y alertas | KPI, hallazgo, acción, revisión y control |
| RN-025 | niveles derivados | matriz 5×5 y límites de bandas |
| RN-026 | cierre condicionado | residual, controles vigentes, revisión y rechazo |
| RNF-004 | servicios atómicos | autoaprobación y cierre sin persistencia parcial |
| ENT-039–043 | riesgos, evaluaciones, controles y revisiones | migración desde cero y constraints |
| ENT-047–050 | versión de control y enlaces explícitos | FK, unicidad y organización |

## Pruebas añadidas

- Límites completos de la matriz 1–25 y rechazo fuera del rango.
- Creación de riesgo y evaluación inherente/residual reproducible.
- Autoaprobación de evaluación bloqueada.
- Evaluación aprobada que actualiza el estado funcional.
- Control versionado y aprobación independiente.
- Vínculo riesgo–control limitado a versiones vigentes.
- Revisión impedida al responsable del riesgo o control.
- Cierre con residual bajo y control revisado.
- Riesgo residual alto impedido sin controles vigentes RN-026.
- Alertas pendiente, tratamiento, ineficaz, próximo y no aplicable.
- Catálogo y detalle HTTP 403/200 con marca sintética.
- Semilla idempotente 20/24/12/24/18 y relaciones contractuales.

## Evaluación actual de G14

Las comprobaciones locales disponibles verificaron documentación, lint, tipado sobre 117 archivos, modelos y ausencia de migraciones pendientes. La ejecución completa sobre PostgreSQL 17 y la aceptación formal siguen pendientes.

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado a P03/P05 | RF-033–035, CU-20, RN-025–026 y entidades | Conforme |
| 2 | Contratos P04/P05 actualizados | dependencias y extensiones explícitas | Conforme |
| 3 | Matriz reproducible | producto 1–25 y bandas documentadas | Conforme |
| 4 | Evaluaciones versionadas | borrador, revisión, aprobación y sustitución | Conforme |
| 5 | Controles versionados | raíz, versión, vigencia y aprobación segregada | Conforme |
| 6 | Relaciones RF-035 | proceso, KPI, hallazgo, acción y control con FK | Conforme |
| 7 | Revisión y alertas | fechas, ineficacia, responsable y precedencia | Conforme |
| 8 | Cierre condicionado RN-026 | residual y controles revisados | Conforme |
| 9 | Historia protegida | `PROTECT`, servicios, bitácora y sin borrado masivo | Conforme |
| 10 | Semilla contractual | 20 riesgos, 24 evaluaciones y relaciones sintéticas | Conforme |
| 11 | CI en Python 3.13/PostgreSQL 17 | Pendiente de ejecución en GitHub | Pendiente |
| 12 | Aceptación formal del titular | Requiere autorización expresa posterior | Pendiente |

**Resultado actual:** 10/12. P14 está **EN PRUEBAS** y G14 permanece abierta. La aprobación interna no representa certificación, autorización sanitaria ni aptitud productiva.
