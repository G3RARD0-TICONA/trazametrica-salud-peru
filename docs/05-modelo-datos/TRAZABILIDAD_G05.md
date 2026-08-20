# Trazabilidad, pruebas y puerta G05

## 1. Requisitos hacia datos

| Requisitos P03 | Entidades P05 | Integridad/evidencia |
|---|---|---|
| RF-001–003 | `accounts_user`, `role`, `user_role` | Desactivación, vigencia de rol y autoría protegida |
| RF-004–005 | `organization`, `site`, `service`, `area`, `responsibility_assignment` | Código por ámbito y ausencia de borrado físico |
| RF-006–009 | `process`, `process_version`, `sipoc_entry`, `document`, `document_version` | Raíz estable, versión única, aprobación e inmutabilidad |
| RF-010–014 | `template`, `template_version`, `import_job`, `import_row`, `import_error`, `file_asset` | Esquema/hash, atomicidad, errores y duplicados |
| RF-015–018 | `indicator`, `indicator_version`, `observation`, `result`, `result_input` | Decimal exacto, fórmula/versiones, entradas y correcciones |
| RF-019–021 | `audit_plan`, `checklist*`, `audit_execution`, `audit_response`, `finding*` | Criterios versionados, respuesta única y evidencia |
| RF-022–024 | `root_cause_analysis`, `corrective_action`, `action_evidence`, `effectiveness_review` | Responsable, fechas, revisión independiente y reapertura |
| RF-025 | `file_asset`, `finding_evidence`, `action_evidence`, `document_version` | Ruta opaca, SHA-256, metadatos y FK específicas |
| RF-026–027 | `auditlog_event` | Evento append-only, correlación, filtros y hash |
| RF-028–030 | Tablas funcionales, `export_contract`, `export_run` | Contrato versionado, filtros y salida trazada |
| RF-031–032 | `reference_source`, `reference_version`, semillas | Referencia sin certificación y demo regenerable |
| RF-033–035 | `risk`, `risk_assessment`, `control`, `risk_control`, `control_review` | Evaluación versionada, vínculos y revisiones |

## 2. Reglas de negocio hacia controles

| Reglas P03 | Control de datos |
|---|---|
| RN-001–002 | UQ por ámbito, B03 y FK `PROTECT` |
| RN-003–006 | B04, versión única, servicios de transición y motivo obligatorio |
| RN-007–010 | Plantilla versionada, hashes, fila/error y transacción de promoción |
| RN-011–013 | `indicator_version`, `result_input`, `numeric(20,6)` y hash de resultado |
| RN-014–019 | Hallazgo, causa, acción, evidencia y revisión de eficacia separadas |
| RN-020–023 | `file_asset`, `export_run`, `auditlog_event` y usuarios desactivables |
| RN-024 | Fuentes como referencia; ninguna columna denominada certificación/cumplimiento |
| RN-025–026 | Comprobación de escalas, evaluación residual y controles vigentes |

## 3. Pruebas de aceptación de datos

| ID | Escenario | Resultado esperado |
|---|---|---|
| PA-05-01 | Crear dos códigos iguales en el mismo ámbito | Segundo registro rechazado por UQ |
| PA-05-02 | Reutilizar código tras desactivar maestro | Operación rechazada; el código histórico permanece reservado |
| PA-05-03 | Eliminar usuario o maestro referenciado | FK protegida impide pérdida de historia |
| PA-05-04 | Crear dos versiones con igual número | Segunda versión rechazada |
| PA-05-05 | Modificar una versión aprobada | Servicio y prueba de repositorio rechazan el cambio |
| PA-05-06 | Aprobar dos versiones vigentes superpuestas | Transacción rechazada; queda una vigencia válida |
| PA-05-07 | Guardar fecha final anterior a la inicial | `CHECK` rechaza la fila |
| PA-05-08 | Registrar archivo sin hash/tamaño válido | Registro rechazado y archivo pendiente limpiable |
| PA-05-09 | Aceptar dos cargas con mismo hash y organización | Restricción parcial rechaza el duplicado |
| PA-05-10 | Promover una carga con error bloqueante | Cero observaciones funcionales incorporadas |
| PA-05-11 | Guardar KPI con `float` o exceso de escala | Modelo exige decimal y validación explícita |
| PA-05-12 | Recalcular con mismas entradas y versión | Mismo valor y `result_hash` |
| PA-05-13 | Publicar resultado sin actor o fecha | `CHECK` rechaza el estado inconsistente |
| PA-05-14 | Registrar respuesta duplicada para un ítem | UQ rechaza la segunda respuesta |
| PA-05-15 | Evaluar riesgo fuera de escala o con nivel incorrecto | `CHECK` rechaza la evaluación |
| PA-05-16 | Ejecutar semilla dos veces | Conteos y claves estables, sin duplicados |
| PA-05-17 | Ejecutar `--reset` en entorno no sintético | Comando se niega antes de borrar datos |
| PA-05-18 | Restaurar DB y archivos con manifiesto alterado | Verificación de hashes impide declarar éxito |

## 4. Riesgos abiertos

| Riesgo | Tratamiento aprobado en P05 | Parte responsable |
|---|---|---|
| Esquema demasiado amplio | 46 tablas alineadas a módulos; implementación incremental | P06–P15 |
| Intervalos superpuestos | Servicio transaccional y pruebas; evaluar restricción de exclusión si es necesario | P08/P09/P11/P17 |
| Inmutabilidad eludida desde SQL | Cuenta DB restringida, servicios y pruebas; trigger solo mediante nueva ADR | P17/P18 |
| `jsonb` se vuelve almacén informal | Solo staging, esquemas/fórmulas versionados, filtros y contexto técnico | Revisiones de P10/P15 |
| Índices sobran o faltan | Registro IX y medición `EXPLAIN` con dataset base | P17 |
| Archivos quedan huérfanos | Estado pendiente, confirmación transaccional y limpiador | P08/P10/P17 |
| Dataset revela información real | Generación desde cero, dominios `.invalid` y pruebas negativas | P10/P17 |
| Migración destruye historia | FK protegidas, backup y prueba de actualización/reversión | Todas las partes |

## 5. Puerta G05

| N.º | Criterio | Estado |
|---:|---|---|
| 1 | Entidades y responsabilidades alineadas con los 12 módulos de P04 | Conforme |
| 2 | Los 35 RF y 26 RN de P03 tienen destino de datos trazable | Conforme |
| 3 | Diccionario físico define tabla, campos, tipos, nulabilidad y claves | Conforme |
| 4 | PK, FK y políticas de borrado están definidas | Conforme |
| 5 | Unicidad y comprobaciones críticas tienen registro verificable | Conforme |
| 6 | Versiones, vigencias e inmutabilidad están modeladas | Conforme |
| 7 | Decimal, fechas, zona horaria, JSON y archivos tienen reglas explícitas | Conforme |
| 8 | Índices responden a consultas previstas y tienen validación futura | Conforme |
| 9 | Migraciones y evolución incompatible tienen procedimiento | Conforme |
| 10 | Dataset sintético es determinista, idempotente y dimensionado | Conforme |
| 11 | Pruebas PA-05 cubren integridad, atomicidad, seguridad y recuperación | Conforme |
| 12 | Aprobación interna del titular registrada | Conforme |

**Resultado final:** 12/12 controles conformes. El titular aceptó el modelo de 46 entidades, sus reglas de integridad y el cierre de G05 el 20 de agosto de 2026.

## 6. Efecto de aprobación

El cierre de G05 habilita la implementación incremental del esqueleto Django/PostgreSQL y P06. No autoriza datos reales, despliegue productivo ni crear las 46 tablas sin migraciones y pruebas. Cada parte implementará únicamente el subconjunto que le corresponde y actualizará este contrato si surge una necesidad aprobada.
