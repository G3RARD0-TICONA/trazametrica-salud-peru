# Trazabilidad y puerta G16

## Requisitos

| Fuente | Evidencia P16 | Verificación |
|---|---|---|
| RF-036 | descriptivos, atípicos, Pareto, control y tendencia | pruebas unitarias deterministas |
| RF-037 | regresión lineal/logística y partición temporal | métricas de prueba y línea base |
| RF-038 | versión, parámetros, supuestos y hashes | modelos, servicios y bitácora |
| CU-21 | catálogo, ejecución y consulta protegidos | prueba web y permisos |
| RN-027 | solo observaciones sintéticas procesadas | relación KPI y marca persistente |
| RN-028 | misma entrada/versión produce mismo hash | ejecución repetida |
| RN-029 | sin fuga y con línea base | puerta de calidad explícita |
| RN-030 | exclusión de uso clínico | interfaz, supuestos y documentación |
| ENT-051–052 | definición y ejecución analítica | migración, constraints e índices |

## Controles G16

| N.° | Control | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado | RF-036–038, CU-21 y RN-027–030 | Conforme |
| 2 | Modelo persistente | ENT-051–052, migración e integridad | Conforme |
| 3 | Estadística reproducible | descriptivos, Pareto, control y medias móviles | Conforme |
| 4 | Modelos predictivos | regresión lineal y logística deterministas | Conforme |
| 5 | Separación entrenamiento/prueba | partición cronológica y métricas de prueba | Conforme |
| 6 | Línea base y rechazo | estado `rejected_quality` verificable | Conforme |
| 7 | Versionado e inmutabilidad | parámetros canónicos y SHA-256 | Conforme |
| 8 | Permisos y segregación | gestionar, aprobar, ejecutar y consultar | Conforme |
| 9 | Trazabilidad y exclusión clínica | bitácora, supuestos y marca sintética | Conforme |
| 10 | Semilla demostrativa | seis definiciones y ejecuciones idempotentes | Conforme |
| 11 | Pruebas, cobertura y CI | suite P16 y workflow del PR | Conforme |
| 12 | Aceptación formal del titular | autorización explícita de cierre e integración | Pendiente |

**Resultado previo a aceptación:** 11/12 controles conformes. G16 permanece abierta y el PR debe permanecer en borrador hasta autorización expresa.

