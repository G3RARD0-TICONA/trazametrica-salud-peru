# Trazabilidad y puerta G12

## Requisitos

| Fuente | Evidencia P12 | Prueba |
|---|---|---|
| RF-019 / CU-10 | `AuditPlan` y flujo de aprobación | fechas, estado y autoaprobación bloqueada |
| RF-020 | lista, versión, criterios, ejecución y respuestas | hash, vigencia, obligatoriedad y unicidad |
| RF-021 / CU-11 | `Finding` y `FindingEvidence` | tipo, impacto, origen, responsable y fecha |
| RN-014 | evidencia o justificación de ausencia | rollback ante registro incompleto |
| RNF-004 | servicios transaccionales | ninguna operación crítica parcial |
| ENT-027–034 | ocho tablas, FK, constraints e índices | migración desde cero y `makemigrations --check` |

## Pruebas añadidas

- Creación, edición, rechazo y aprobación independiente de plan.
- Lista con hash, criterios obligatorios y versión vigente.
- Inicio bloqueado sin plan aprobado o lista vigente.
- Respuesta única, pertenencia a lista y justificación obligatoria.
- Hallazgo incompleto rechazado sin persistencia parcial.
- Evidencia sintética limpia vinculada y trazable.
- Envío bloqueado por criterios pendientes o no conformidad sin hallazgo.
- Revisión, devolución y término independiente.
- Cancelación motivada y ausencia de eliminación física.
- Catálogo HTTP 403/200 con marca sintética.
- Alertas vencido, próximo y en plazo.
- Semilla idempotente 12/3/12/180/180/12.

## Evaluación actual de G12

Las verificaciones locales aprobaron 114 pruebas aplicables y 83 % de cobertura. La comprobación PostgreSQL integral y la aceptación formal siguen pendientes.

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado a P03/P05 | RF, CU, RN, RNF y ENT identificadas | Conforme |
| 2 | ENT-027–034 implementadas | modelos, migración, constraints e índices | Conforme |
| 3 | Planificación segregada | autor, aprobador, motivo y fechas | Conforme |
| 4 | Lista versionada e íntegra | contenido ordenado, hash, vigencia e inmutabilidad | Conforme |
| 5 | Ejecución reproducible | plan, versión, respuestas, actores y fechas | Conforme |
| 6 | Registro completo RN-014 | criterio, condición, clasificación y origen | Conforme |
| 7 | Evidencia sintética RN-020 | metadatos, SHA-256, escaneo o justificación | Conforme |
| 8 | Revisión independiente | auditor líder no aprueba su ejecución | Conforme |
| 9 | Consulta y alertas | HTTP protegido y vencimiento derivado | Conforme |
| 10 | Semilla contractual | 12 planes, 180 respuestas y 180 hallazgos | Conforme |
| 11 | CI en Python 3.13/PostgreSQL 17 | Pendiente de ejecución en GitHub | Pendiente |
| 12 | Aceptación formal del titular | Requiere autorización expresa posterior | Pendiente |

**Resultado actual:** 10/12. P12 está **EN PRUEBAS** y G12 permanece abierta. La aprobación interna no representa certificación, autorización sanitaria ni aptitud productiva.
