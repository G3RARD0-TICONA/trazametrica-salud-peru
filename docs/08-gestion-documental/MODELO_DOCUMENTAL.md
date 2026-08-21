# Modelo documental

## 1. Entidades implementadas

| P05 | Modelo Django | Tabla PostgreSQL | Función |
|---|---|---|---|
| ENT-012 | `FileAsset` | `documents_file_asset` | Metadatos íntegros de un archivo sintético |
| ENT-013 | `Document` | `documents_document` | Identidad, tipo y responsabilidad documental |
| ENT-014 | `DocumentVersion` | `documents_document_version` | Contenido, estado, vigencia y aprobación |
| ENT-015 | `ReferenceSource` | `documents_reference_source` | Identidad de una fuente de referencia |
| ENT-016 | `ReferenceVersion` | `documents_reference_version` | Evidencia consultada y versionada |
| ENT-046 | `AuditEvent` | `auditlog_event` | Evento inmutable de trazabilidad |

## 2. Relaciones

```text
Organization 1 ── N Document N ── 1 Area responsable
                         │
                         └── N DocumentVersion ── 0..1 FileAsset

ReferenceSource 1 ── N ReferenceVersion

User 1 ── N creación / envío / revisión / aprobación / desactivación
AuditEvent N ── 0..1 User y referencia lógica al objeto afectado
```

## 3. Integridad

- El código de documento es único por organización sin distinguir mayúsculas.
- El código de referencia es único en la instalación sin distinguir mayúsculas.
- Cada documento y referencia usa una secuencia única de números de versión desde 1.
- Una versión documental contiene texto o un archivo limpio, no ambos ni ninguno.
- Los hashes SHA-256 tienen 64 caracteres hexadecimales y permiten detectar cambios.
- Todas las claves foráneas usan `PROTECT`.
- Los registros documentales y eventos de bitácora bloquean eliminación física.
- Los maestros se desactivan con fecha, actor y motivo después de cerrar sus versiones abiertas.

## 4. Autoría y segregación

Creación y modificación conservan actor. El envío registra `submitted_by/at`; rechazo o revisión registra `reviewed_by/at`; aprobación registra además `approved_by/at`. El servicio rechaza que `created_by` y `approved_by` sean la misma persona, incluso si esa persona posee capacidad de aprobación.

## 5. Hash de versión

El hash de `DocumentVersion` se calcula de forma determinista con identificador del documento, número de versión, contenido normalizado y SHA-256 del archivo si existe. Cambiar cualquiera de esos componentes genera otro hash. Al salir de borrador, contenido, archivo, secuencia y hash se vuelven inmutables.

