# Integridad, historización e índices

## 1. Claves y relaciones

- Toda PK del dominio es `uuid`; las semillas usan UUID deterministas y las operaciones ordinarias UUID aleatorios.
- Toda FK se declara explícitamente en Django y PostgreSQL. No se guardan relaciones funcionales únicamente dentro de `jsonb`.
- Las FK históricas usan `PROTECT`; una cuenta, maestro, versión, archivo o resultado referenciado no se elimina físicamente.
- El MVP no utilizará borrado en cascada entre tablas del dominio. El restablecimiento de demo reconstruye el esquema/dataset mediante un comando controlado.
- Una relación opcional solo admite `NULL` cuando la ausencia tiene significado documentado; no se usan UUID vacíos ni códigos como sustituto de `NULL`.
- `organization_id` delimita códigos y consultas aunque ADR-005 establezca una organización por instalación.

## 2. Unicidad mínima

| ID | Regla |
|---|---|
| UQ-05-01 | `accounts_user.username` normalizado es único |
| UQ-05-02 | `accounts_role.code` es único |
| UQ-05-03 | Un usuario no repite el mismo rol y fecha de inicio |
| UQ-05-04 | `organizations_organization.code` es único |
| UQ-05-05 | Sede única por `(organization_id, code)` |
| UQ-05-06 | Servicio único por `(site_id, code)` |
| UQ-05-07 | Área única por `(organization_id, code)` |
| UQ-05-08 | Proceso único por `(organization_id, code)` |
| UQ-05-09 | Versión de proceso única por `(process_id, version_no)` |
| UQ-05-10 | Posición SIPOC única por `(process_version_id, entry_type, position)` |
| UQ-05-11 | `documents_file_asset.storage_key` es único |
| UQ-05-12 | Documento único por `(organization_id, code)` |
| UQ-05-13 | Versión documental única por `(document_id, version_no)` |
| UQ-05-14 | Fuente normativa única por `code` y versión única por `(reference_source_id, version_no)` |
| UQ-05-15 | Plantilla única por `(organization_id, code)` y versión única por `(template_id, version_no)` |
| UQ-05-16 | Un archivo aceptado/promovido no repite `(organization_id, file_hash)` |
| UQ-05-17 | Fila única por `(import_job_id, row_number)` |
| UQ-05-18 | Indicador único por `(organization_id, code)` y versión única por `(indicator_id, version_no)` |
| UQ-05-19 | `indicator_result.result_hash` es único y cada vínculo `(result_id, observation_id)` no se repite |
| UQ-05-20 | Plan, lista, hallazgo y acción conservan códigos únicos dentro de su organización/objeto padre |
| UQ-05-21 | Respuesta única por `(execution_id, checklist_item_id)` |
| UQ-05-22 | Evaluación de riesgo única por `(risk_id, version_no)` y vínculo único por `(risk_id, control_version_id, valid_from)` |
| UQ-05-23 | Contrato de exportación único por `(code, version_no)` |
| UQ-05-24 | `auditlog_event.event_hash` es único |
| UQ-05-25 | Versión de control única por `(control_id, version_no)` |
| UQ-05-26 | Los vínculos `(risk_id, indicator_id)`, `(risk_id, finding_id)` y `(risk_id, action_id)` no se repiten |

Las condiciones de unicidad parcial —por ejemplo, un solo trabajo promovido para un hash— se implementan con `UniqueConstraint(condition=...)`. La prevención de intervalos de vigencia superpuestos se completa en servicio y con pruebas transaccionales.

## 3. Comprobaciones de dominio

| ID | Regla comprobable en base |
|---|---|
| CK-05-01 | Todo `version_no >= 1` y toda `position >= 1` |
| CK-05-02 | `valid_to IS NULL OR valid_to >= valid_from` |
| CK-05-03 | Una desactivación exige instante, actor y motivo; un registro activo no los tiene |
| CK-05-04 | `size_bytes > 0` y los hashes SHA-256 tienen 64 caracteres |
| CK-05-05 | Un `DocumentVersion` contiene archivo o contenido, nunca ambos vacíos |
| CK-05-06 | `row_count >= 0`, `error_count >= 0` y `error_count <= row_count` |
| CK-05-07 | `attempt_count >= 0` y `finished_at >= started_at` cuando ambos existen |
| CK-05-08 | `row_number >= 1` y una fila inválida puede tener uno o más errores |
| CK-05-09 | Severidad de error pertenece a `warning` o `blocking` |
| CK-05-10 | `period_end >= period_start` en observaciones y resultados |
| CK-05-11 | Un resultado publicado tiene `published_at` y `published_by_id`; uno no publicado no los tiene |
| CK-05-12 | `supersedes_id` no puede ser el propio resultado |
| CK-05-13 | Fechas planificadas de auditoría cumplen `planned_end >= planned_start` |
| CK-05-14 | `completed_at >= started_at` en ejecuciones |
| CK-05-15 | Una respuesta requerida no puede guardar resultado vacío |
| CK-05-16 | Una acción completada tiene `completed_at`; una pendiente no lo tiene |
| CK-05-17 | Probabilidad e impacto están entre 1 y 5 |
| CK-05-18 | `inherent_level = probability * impact` |
| CK-05-19 | Los tres valores residuales son todos nulos o todos informados y el nivel es su producto |
| CK-05-20 | `valid_to >= valid_from` en relación riesgo–control |
| CK-05-21 | `row_count >= 0` en exportaciones y su hash tiene 64 caracteres |
| CK-05-22 | Resultado de evento pertenece a `success`, `denied`, `error` o `cancelled` |
| CK-05-23 | Solo el usuario técnico inicial puede tener `created_by IS NULL`, ser superusuario y registrar `bootstrap_reason` |
| CK-05-24 | La clasificación inherente y residual corresponde al nivel calculado según las bandas aprobadas |
| CK-05-25 | Una versión de control vigente tiene fecha inicial, fecha y actor de aprobación |
| CK-05-26 | La próxima revisión de un control es posterior a la revisión realizada |

Las reglas que consultan otras filas o tablas —autoaprobación, solapamiento, transición y eficacia— se ejecutan dentro de servicios transaccionales. La base continúa protegiendo nulabilidad, tipos, FK, unicidad y comprobaciones locales.

### Estados físicos permitidos

| Familia | Valores persistidos |
|---|---|
| Versiones | `draft`, `in_review`, `approved`, `effective`, `superseded`, `annulled` |
| Importación | `received`, `validating`, `rejected`, `accepted`, `processing`, `processed`, `failed` |
| Resultado KPI | `calculated`, `in_review`, `rejected`, `published`, `corrected` |
| Auditoría | `planned`, `in_progress`, `completed`, `closed`, `cancelled` |
| Hallazgo | `open`, `under_analysis`, `with_plan`, `under_verification`, `closed`, `reopened` |
| Acción | `pending`, `in_progress`, `under_verification`, `effective`, `ineffective`, `closed`, `reopened` |
| Riesgo | `identified`, `assessed`, `under_treatment`, `controlled`, `accepted`, `closed`, `reopened` |
| Evaluación de riesgo | `draft`, `in_review`, `approved`, `superseded` |
| Versión de control | `draft`, `in_review`, `effective`, `superseded`, `annulled` |
| Escaneo de archivo | `pending`, `clean`, `rejected`, `error` |
| Contrato de exportación | `draft`, `published`, `superseded`, `annulled` |

Cada familia se implementará con `TextChoices` y `CheckConstraint`; mostrar etiquetas en español no cambia el valor físico estable.

## 4. Versiones e inmutabilidad

| Raíz | Tabla de versión | Identidad estable | Contenido inmutable al aprobar |
|---|---|---|---|
| `process` | `process_version` | Código, organización, propietario | Objetivo, alcance, SIPOC, vigencia y hash |
| `document` | `document_version` | Código, tipo, proceso | Archivo/contenido, vigencia y hash |
| `reference_source` | `reference_version` | Emisor, código, título | Fecha, resumen, enlace consultado y hash |
| `import_template` | `template_version` | Código y destino | Esquema, plantilla, vigencia y hash |
| `indicator` | `indicator_version` | Código, proceso, responsable | Fórmula, unidad, frecuencia, meta y umbrales |
| `checklist` | `checklist_version` | Código y nombre | Ítems, orden, criterios y obligatoriedad |
| `control` | `control_version` | Código, organización y responsable | Descripción, tipo, frecuencia, vigencia y aprobación |
| `export_contract` | misma tabla por versión | Código y nombre | Columnas, tipos, orden, formato y hash |

La aplicación rechazará `UPDATE` y `DELETE` de una versión aprobada. P17 deberá probar la restricción desde interfaz, servicio y operación directa autorizada de prueba. No se agregará un disparador PostgreSQL en el MVP sin una nueva ADR, porque ocultaría lógica fuera del ORM; la defensa se basa en servicios, permisos de la cuenta DB y pruebas.

## 5. Índices previstos

| ID | Tabla y columnas | Consulta que justifica el índice |
|---|---|---|
| IX-05-01 | `accounts_user (is_active, username)` | Inicio de sesión y usuarios activos |
| IX-05-02 | `accounts_user_role (user_id, valid_from, valid_to)` | Roles vigentes |
| IX-05-03 | `organizations_service (site_id, is_active, code)` | Catálogo por sede |
| IX-05-04 | `organizations_area (organization_id, parent_id)` | Jerarquía de áreas |
| IX-05-05 | `processes_process (organization_id, is_active, code)` | Búsqueda de procesos |
| IX-05-06 | `processes_process_version (process_id, status, -version_no)` | Versión vigente y últimas versiones |
| IX-05-07 | `documents_document (organization_id, process_id, is_active)` | Documentos por proceso |
| IX-05-08 | `documents_document_version (document_id, status, -version_no)` | Vigencia documental |
| IX-05-09 | `documents_file_asset (sha256)` | Detección y comprobación de contenido |
| IX-05-10 | `imports_import_job (organization_id, status, -created_at)` | Cola e historial de cargas |
| IX-05-11 | `imports_import_job (organization_id, file_hash)` | Duplicados de archivo |
| IX-05-12 | `imports_import_row (import_job_id, is_valid, row_number)` | Validación y promoción |
| IX-05-13 | `imports_import_error (import_row_id, severity)` | Errores por fila |
| IX-05-14 | `indicators_observation (indicator_id, period_start, period_end)` | Serie por indicador |
| IX-05-15 | `indicators_observation (site_id, service_id, period_start)` | Filtros de tablero |
| IX-05-16 | `indicators_result (indicator_version_id, period_start, status)` | Publicación y tendencias |
| IX-05-17 | `audits_audit_plan (organization_id, status, planned_start)` | Plan anual y pendientes |
| IX-05-18 | `audits_finding (status, due_date, owner_id)` | Hallazgos vencidos |
| IX-05-19 | `improvements_corrective_action (status, due_date, owner_id)` | Acciones y alertas |
| IX-05-20 | `risks_risk (organization_id, process_id, status)` | Matriz de riesgos |
| IX-05-21 | `risks_control_review (next_review_date)` y FK `risk_control_id` | Controles por revisar y su asignación exacta |
| IX-05-22 | `reports_export_run (requested_by_id, -generated_at)` | Historial de exportaciones |
| IX-05-23 | `auditlog_event (object_type, object_id, -occurred_at)` | Historia de un objeto |
| IX-05-24 | `auditlog_event (correlation_id, occurred_at)` | Trazabilidad de operación |

Django crea índices habituales para FK, pero cada migración deberá inspeccionarse para evitar duplicados. Los índices compuestos se validarán con el conjunto de referencia y `EXPLAIN (ANALYZE, BUFFERS)` en P17; no se agregarán índices por intuición.

## 6. Archivos y consistencia

1. Se crea `FileAsset` con estado de carga pendiente y clave opaca.
2. El archivo se escribe en almacenamiento privado y se calcula SHA-256.
3. La transacción funcional enlaza el activo y confirma sus metadatos.
4. Si falla la transacción, un limpiador elimina archivos huérfanos pendientes; nunca borra un archivo enlazado.
5. Backup y restauración comparan manifiesto, hashes y FK antes de declarar éxito.

La base no almacena contenido binario, rutas públicas ni el nombre original como ruta física.
