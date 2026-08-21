# Trazabilidad y puerta G10

## 1. Requisitos cubiertos

| Fuente | Evidencia P10 | Prueba |
|---|---|---|
| RF-010/CU-06 | plantilla identificada por código, versión y hash | generación, descarga y metadatos |
| RF-011 | archivo, plantilla, hash, actor, fecha y estado | `FileAsset` e `ImportJob` |
| RF-012 | estructura, tipos, obligatoriedad, códigos, fechas, rangos y duplicados | validaciones positivas/negativas |
| RF-013/RN-008 | rechazo completo y errores por fila/columna/regla | promoción bloqueada |
| RF-014/RN-009 | hash único aceptado, antecedente y reintento | duplicado y `retry_of` |
| RN-007 | identidad exacta de versión | hoja META y `schema_hash` |
| RN-010 | fecha futura solo planificada | `allow_future` y prueba negativa |
| RNF-007 | 10 000 filas en ≤60 s | prueba de carga automatizada |
| ENT-017–021 | modelos, constraints, índices y migración | correspondencia física |

## 2. Pruebas añadidas

- Normalización, unicidad, hash y aprobación independiente de plantilla.
- XLSX determinista e identificado.
- Carga válida, promoción y auditoría.
- Errores accionables de patrón, fecha, tipo, rango, catálogo y duplicado.
- Identidad de plantilla alterada.
- Fórmula Excel bloqueada.
- Archivo aceptado duplicado vinculado a antecedente.
- Reintento de carga rechazada.
- Confirmación sintética y permiso obligatorios.
- Correo real bloqueado sin copiarlo al mensaje.
- Sustitución de versión vigente.
- Registros sin eliminación física.
- Semilla idempotente de 4 plantillas/4 versiones.
- HTTP 403/200 y descarga con `nosniff`.
- Contenedor falso y objeto incrustado rechazados.
- Esquemas inseguros o inconsistentes rechazados.
- 10 000 filas dentro del límite de 60 segundos.

## 3. Evaluación actual de G10

Las verificaciones locales aprobaron 88 pruebas aplicables y 85 % de cobertura. CI y aceptación formal siguen pendientes.

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado a P03/P05 | RF, CU, RN, RNF y ENT identificadas | Conforme |
| 2 | ENT-017–021 implementadas | modelos, migración, constraints e índices | Conforme |
| 3 | Plantillas identificadas y versionadas | código, versión, esquema, hash y vigencia | Conforme |
| 4 | Publicación independiente e inmutable | autor/aprobador y prueba negativa | Conforme |
| 5 | Validación funcional completa | estructura, columnas, tipos y reglas | Conforme |
| 6 | Rechazo atómico y errores accionables | staging, errores y promoción bloqueada | Conforme |
| 7 | Duplicados y reintentos trazables | SHA-256, antecedente e intento | Conforme |
| 8 | Seguridad y datos sintéticos | OOXML seguro, fórmulas bloqueadas y `.invalid` | Conforme |
| 9 | Consulta, descarga y carga autorizadas | rutas protegidas y prueba HTTP | Conforme |
| 10 | Semilla y rendimiento de referencia | 4 plantillas y 10 000 filas ≤60 s | Conforme |
| 11 | CI en Python 3.13/PostgreSQL 17 | Pendiente de ejecución en GitHub | Pendiente |
| 12 | Aceptación formal del titular | Requiere autorización expresa posterior | Pendiente |

**Resultado actual:** 10/12. P10 está **EN PRUEBAS** y G10 permanece abierta. La aceptación interna no representa certificación, autorización sanitaria ni aptitud productiva.
