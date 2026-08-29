# Trazabilidad y puerta G15

## Requisitos

| Fuente | Evidencia P15 | Verificación |
|---|---|---|
| RF-028 | tablero y filtros combinables | consulta web y selectores |
| RF-029 / CU-16 | CSV, XLSX y PDF | firmas, contenido, permisos e historial |
| RF-030 | contrato CSV estable | consumidor Power BI Desktop y orden de columnas |
| RN-021 | marca, versión, fecha y filtros | metadatos en archivo y ejecución |
| RNF-014 | contrato versionado | hash, sustitución e incompatibilidad bloqueada |
| ENT-044–045 | contrato y ejecución | migración, FK, constraints e índices |

## Evaluación actual de G15

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado | RF-028–030, CU-16, RN-021 y RNF-014 | Conforme |
| 2 | Modelo físico | ENT-044/045, migración, FK y constraints | Conforme |
| 3 | Filtros RF-028 | periodo, sede, servicio, proceso, indicador y estado | Conforme |
| 4 | Versionado RNF-014 | versión, esquema canónico, hash y sustitución | Conforme |
| 5 | Excel y CSV | OOXML controlado, UTF-8 y neutralización de fórmulas | Conforme |
| 6 | PDF | documento paginado con metadatos y marca | Conforme |
| 7 | Power BI Desktop | CSV estable sin servicio externo | Conforme |
| 8 | Metadatos RN-021 | contrato, fecha, filtros y marca sintética | Conforme |
| 9 | Autorización e historia | capacidades, `PROTECT`, bitácora y sin borrado | Conforme |
| 10 | Semilla contractual | siete contratos deterministas e idempotentes | Conforme |
| 11 | CI PostgreSQL 17 | CI #67: 151 pruebas, 82 %, seguridad, dependencias e imagen conformes | Conforme |
| 12 | Aceptación formal | autorización expresa registrada el 29 de agosto de 2026 | Conforme |

**Resultado final:** 12/12. P15 está **APROBADA INTERNAMENTE** y G15 queda cerrada. Esta aprobación interna no representa certificación, autorización sanitaria ni aptitud productiva.
