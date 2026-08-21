# Diccionario físico de datos

## 1. Convenciones

Leyenda: `!` obligatorio, `?` opcional, `PK` clave primaria y `FK` clave foránea. Todos los nombres físicos usan `snake_case`; tablas e índices incluyen el prefijo de su aplicación.

| Tipo lógico | Django | PostgreSQL | Uso |
|---|---|---|---|
| Identificador | `UUIDField` | `uuid` | PK y FK del dominio |
| Código | `CharField(max_length=50)` | `varchar(50)` | Identidad funcional normalizada |
| Nombre | `CharField(max_length=200)` | `varchar(200)` | Etiqueta visible |
| Texto corto | `CharField(max_length=500)` | `varchar(500)` | Motivos y resúmenes acotados |
| Texto largo | `TextField` | `text` | Descripción o contenido administrativo |
| Estado | `CharField` + `TextChoices` | `varchar(30)` | Flujo validado por servicio y `CHECK` |
| Entero | `IntegerField` | `integer` | Versión, orden y conteo |
| Valor exacto | `DecimalField(20,6)` | `numeric(20,6)` | Observaciones y resultados KPI |
| Porcentaje | `DecimalField(7,4)` | `numeric(7,4)` | Proporciones de 0 a 100 |
| Fecha | `DateField` | `date` | Periodo, vigencia y vencimiento |
| Instante | `DateTimeField` | `timestamptz` | Evento inequívoco almacenado en UTC |
| Documento variable | `JSONField` | `jsonb` | Staging, filtros o contexto versionado |

## 2. Bloques reutilizables

| Bloque | Campos |
|---|---|
| B01 Identidad | `id:uuid PK!` |
| B02 Autoría | `created_at:timestamptz!`; `created_by:uuid FK!`; `updated_at:timestamptz!`; `updated_by:uuid FK!` |
| B03 Ciclo de vida | `is_active:boolean!`; `deactivated_at:timestamptz?`; `deactivated_by:uuid FK?`; `deactivation_reason:varchar(500)?` |
| B04 Versión | `version_no:integer!`; `status:varchar(30)!`; `valid_from:date?`; `valid_to:date?`; `approved_at:timestamptz?`; `approved_by:uuid FK?`; `decision_reason:varchar(500)?` |

## 3. Cuentas y organización

| ID | Tabla | Bloques | Campos específicos |
|---|---|---|---|
| ENT-001 | `accounts_user` | B01, B03 | `username:varchar(150)!`; `email:varchar(254)?`; `password:varchar(128)!`; `first_name:varchar(150)!`; `last_name:varchar(150)!`; `is_staff:boolean!`; `is_superuser:boolean!`; `last_login:timestamptz?`; `created_at:timestamptz!`; `created_by:uuid FK?`; `updated_at:timestamptz!`; `updated_by:uuid FK?`; `bootstrap_reason:varchar(500)?` |
| ENT-002 | `accounts_role` | B01, B02, B03 | `code:varchar(50)!`; `name:varchar(200)!`; `description:text?`; `is_approval_role:boolean!` |
| ENT-003 | `accounts_user_role` | B01, B02 | `user_id:uuid FK!`; `role_id:uuid FK!`; `valid_from:date!`; `valid_to:date?`; `assigned_by_id:uuid FK!` |
| ENT-004 | `organizations_organization` | B01, B02, B03 | `code:varchar(50)!`; `name:varchar(200)!`; `timezone:varchar(64)!`; `demo_label:varchar(100)!` |
| ENT-005 | `organizations_site` | B01, B02, B03 | `organization_id:uuid FK!`; `code:varchar(50)!`; `name:varchar(200)!` |
| ENT-006 | `organizations_service` | B01, B02, B03 | `site_id:uuid FK!`; `code:varchar(50)!`; `name:varchar(200)!` |
| ENT-007 | `organizations_area` | B01, B02, B03 | `organization_id:uuid FK!`; `parent_id:uuid FK?`; `code:varchar(50)!`; `name:varchar(200)!` |
| ENT-008 | `organizations_responsibility_assignment` | B01, B02 | `area_id:uuid FK!`; `user_id:uuid FK!`; `responsibility_type:varchar(30)!`; `valid_from:date!`; `valid_to:date?` |

## 4. Procesos y documentos

| ID | Tabla | Bloques | Campos específicos |
|---|---|---|---|
| ENT-009 | `processes_process` | B01, B02, B03 | `organization_id:uuid FK!`; `code:varchar(50)!`; `name:varchar(200)!`; `process_type:varchar(30)!`; `owner_area_id:uuid FK!` |
| ENT-010 | `processes_process_version` | B01, B02, B04 | `process_id:uuid FK!`; `objective:text!`; `scope:text!`; `version_hash:varchar(64)!`; `submitted_at:timestamptz?`; `submitted_by:uuid FK?`; `reviewed_at:timestamptz?`; `reviewed_by:uuid FK?` |
| ENT-011 | `processes_sipoc_entry` | B01, B02 | `process_version_id:uuid FK!`; `entry_type:varchar(20)!`; `position:integer!`; `name:varchar(200)!`; `description:text?` |
| ENT-012 | `documents_file_asset` | B01, B02 | `storage_key:varchar(500)!`; `original_name:varchar(255)!`; `media_type:varchar(150)!`; `size_bytes:bigint!`; `sha256:varchar(64)!`; `scan_status:varchar(20)!`; `synthetic_confirmed:boolean!` |
| ENT-013 | `documents_document` | B01, B02, B03 | `organization_id:uuid FK!`; `responsible_area_id:uuid FK!`; `process_id:uuid FK?`; `code:varchar(50)!`; `title:varchar(300)!`; `document_type:varchar(30)!` |
| ENT-014 | `documents_document_version` | B01, B02, B04 | `document_id:uuid FK!`; `file_asset_id:uuid FK?`; `content:text?`; `version_hash:varchar(64)!` |
| ENT-015 | `documents_reference_source` | B01, B02, B03 | `code:varchar(50)!`; `issuer:varchar(200)!`; `title:varchar(500)!`; `source_url:varchar(1000)?`; `reference_type:varchar(30)!` |
| ENT-016 | `documents_reference_version` | B01, B02, B04 | `reference_source_id:uuid FK!`; `publication_date:date?`; `consulted_at:timestamptz!`; `summary:text!`; `content_hash:varchar(64)?` |

## 5. Importaciones e indicadores

| ID | Tabla | Bloques | Campos específicos |
|---|---|---|---|
| ENT-017 | `imports_template` | B01, B02, B03 | `organization_id:uuid FK!`; `code:varchar(50)!`; `name:varchar(200)!`; `target_type:varchar(30)!` |
| ENT-018 | `imports_template_version` | B01, B02, B04 | `template_id:uuid FK!`; `schema_definition:jsonb!`; `file_asset_id:uuid FK?`; `schema_hash:varchar(64)!` |
| ENT-019 | `imports_import_job` | B01, B02 | `template_version_id:uuid FK!`; `source_file_id:uuid FK!`; `organization_id:uuid FK!`; `status:varchar(30)!`; `file_hash:varchar(64)!`; `row_count:integer!`; `error_count:integer!`; `started_at:timestamptz?`; `finished_at:timestamptz?`; `promoted_at:timestamptz?`; `attempt_count:integer!` |
| ENT-020 | `imports_import_row` | B01 | `import_job_id:uuid FK!`; `row_number:integer!`; `raw_data:jsonb!`; `normalized_hash:varchar(64)!`; `is_valid:boolean!` |
| ENT-021 | `imports_import_error` | B01 | `import_row_id:uuid FK!`; `column_name:varchar(100)?`; `rule_code:varchar(50)!`; `severity:varchar(20)!`; `message:varchar(500)!`; `suggested_action:varchar(500)?` |
| ENT-022 | `indicators_indicator` | B01, B02, B03 | `organization_id:uuid FK!`; `process_id:uuid FK!`; `code:varchar(50)!`; `name:varchar(200)!`; `owner_id:uuid FK!` |
| ENT-023 | `indicators_indicator_version` | B01, B02, B04 | `indicator_id:uuid FK!`; `unit:varchar(30)!`; `frequency:varchar(20)!`; `direction:varchar(20)!`; `formula_ast:jsonb!`; `formula_hash:varchar(64)!`; `target_value:numeric(20,6)?`; `warning_threshold:numeric(20,6)?` |
| ENT-024 | `indicators_observation` | B01, B02 | `indicator_id:uuid FK!`; `import_job_id:uuid FK!`; `site_id:uuid FK?`; `service_id:uuid FK?`; `period_start:date!`; `period_end:date!`; `value:numeric(20,6)!`; `dimension_key:varchar(200)!`; `source_row_id:uuid FK?` |
| ENT-025 | `indicators_result` | B01, B02 | `indicator_version_id:uuid FK!`; `site_id:uuid FK?`; `service_id:uuid FK?`; `period_start:date!`; `period_end:date!`; `value:numeric(20,6)!`; `status:varchar(30)!`; `calculated_at:timestamptz!`; `published_at:timestamptz?`; `published_by_id:uuid FK?`; `result_hash:varchar(64)!`; `supersedes_id:uuid FK?` |
| ENT-026 | `indicators_result_input` | B01 | `result_id:uuid FK!`; `observation_id:uuid FK!`; `input_role:varchar(30)!`; `position:integer!` |

## 6. Auditoría y mejora

| ID | Tabla | Bloques | Campos específicos |
|---|---|---|---|
| ENT-027 | `audits_audit_plan` | B01, B02, B03 | `organization_id:uuid FK!`; `code:varchar(50)!`; `scope:text!`; `criteria:text!`; `lead_auditor_id:uuid FK!`; `planned_start:date!`; `planned_end:date!`; `status:varchar(30)!` |
| ENT-028 | `audits_checklist` | B01, B02, B03 | `organization_id:uuid FK!`; `code:varchar(50)!`; `name:varchar(200)!` |
| ENT-029 | `audits_checklist_version` | B01, B02, B04 | `checklist_id:uuid FK!`; `version_hash:varchar(64)!` |
| ENT-030 | `audits_checklist_item` | B01, B02 | `checklist_version_id:uuid FK!`; `position:integer!`; `criterion:text!`; `response_type:varchar(20)!`; `is_required:boolean!` |
| ENT-031 | `audits_audit_execution` | B01, B02 | `audit_plan_id:uuid FK!`; `checklist_version_id:uuid FK!`; `started_at:timestamptz?`; `completed_at:timestamptz?`; `status:varchar(30)!` |
| ENT-032 | `audits_audit_response` | B01, B02 | `execution_id:uuid FK!`; `checklist_item_id:uuid FK!`; `result:varchar(20)!`; `observation:text?`; `responded_by_id:uuid FK!`; `responded_at:timestamptz!` |
| ENT-033 | `audits_finding` | B01, B02 | `execution_id:uuid FK!`; `code:varchar(50)!`; `finding_type:varchar(30)!`; `criterion:text!`; `condition:text!`; `impact:varchar(20)!`; `status:varchar(30)!`; `owner_id:uuid FK!`; `due_date:date?` |
| ENT-034 | `audits_finding_evidence` | B01, B02 | `finding_id:uuid FK!`; `file_asset_id:uuid FK!`; `description:varchar(500)!` |
| ENT-035 | `improvements_root_cause_analysis` | B01, B02 | `finding_id:uuid FK!`; `method:varchar(30)!`; `analysis:text!`; `conclusion:text!`; `approved_at:timestamptz?`; `approved_by_id:uuid FK?` |
| ENT-036 | `improvements_corrective_action` | B01, B02 | `finding_id:uuid FK!`; `code:varchar(50)!`; `description:text!`; `owner_id:uuid FK!`; `due_date:date!`; `status:varchar(30)!`; `effectiveness_criterion:text!`; `completed_at:timestamptz?` |
| ENT-037 | `improvements_action_evidence` | B01, B02 | `action_id:uuid FK!`; `file_asset_id:uuid FK!`; `description:varchar(500)!` |
| ENT-038 | `improvements_effectiveness_review` | B01, B02 | `action_id:uuid FK!`; `reviewer_id:uuid FK!`; `reviewed_at:timestamptz!`; `result:varchar(20)!`; `notes:text!`; `reopens_action:boolean!` |

## 7. Riesgos, reportes y bitácora

| ID | Tabla | Bloques | Campos específicos |
|---|---|---|---|
| ENT-039 | `risks_risk` | B01, B02, B03 | `organization_id:uuid FK!`; `process_id:uuid FK!`; `code:varchar(50)!`; `cause:text!`; `event:text!`; `consequence:text!`; `owner_id:uuid FK!`; `status:varchar(30)!` |
| ENT-040 | `risks_risk_assessment` | B01, B02 | `risk_id:uuid FK!`; `version_no:integer!`; `probability:smallint!`; `impact:smallint!`; `inherent_level:smallint!`; `residual_probability:smallint?`; `residual_impact:smallint?`; `residual_level:smallint?`; `assessed_at:timestamptz!`; `approved_at:timestamptz?`; `approved_by_id:uuid FK?` |
| ENT-041 | `risks_control` | B01, B02, B03 | `organization_id:uuid FK!`; `code:varchar(50)!`; `name:varchar(200)!`; `description:text!`; `owner_id:uuid FK!`; `frequency:varchar(20)!` |
| ENT-042 | `risks_risk_control` | B01, B02 | `risk_id:uuid FK!`; `control_id:uuid FK!`; `valid_from:date!`; `valid_to:date?`; `effectiveness_expected:varchar(20)!` |
| ENT-043 | `risks_control_review` | B01, B02 | `control_id:uuid FK!`; `reviewer_id:uuid FK!`; `reviewed_at:timestamptz!`; `result:varchar(20)!`; `notes:text!`; `next_review_date:date!` |
| ENT-044 | `reports_export_contract` | B01, B02, B04 | `code:varchar(50)!`; `name:varchar(200)!`; `format:varchar(20)!`; `schema_definition:jsonb!`; `schema_hash:varchar(64)!` |
| ENT-045 | `reports_export_run` | B01, B02 | `contract_id:uuid FK!`; `requested_by_id:uuid FK!`; `filters:jsonb!`; `file_asset_id:uuid FK!`; `row_count:integer!`; `generated_at:timestamptz!`; `output_hash:varchar(64)!` |
| ENT-046 | `auditlog_event` | B01 | `occurred_at:timestamptz!`; `actor_id:uuid FK?`; `correlation_id:uuid!`; `object_type:varchar(100)!`; `object_id:uuid?`; `action:varchar(50)!`; `result:varchar(20)!`; `reason:varchar(500)?`; `context:jsonb!`; `event_hash:varchar(64)!` |

## 8. Regla de implementación

El diccionario es el contrato de P05. P06–P15 podrán añadir campos justificados, pero cualquier cambio de tipo, nulabilidad, clave, cardinalidad o semántica deberá actualizar este archivo, la migración, la restricción afectada y las pruebas de trazabilidad.

P08 materializa ENT-013 con `responsible_area_id` obligatorio. P09 materializa ENT-009–011 y añade `process_id` a ENT-013 mediante una clave foránea opcional y protegida. También extiende ENT-009 con clasificación del proceso y ENT-010 con evidencia de envío y revisión; estos campos sustentan catálogo, segregación y auditoría sin alterar las cardinalidades aprobadas.
