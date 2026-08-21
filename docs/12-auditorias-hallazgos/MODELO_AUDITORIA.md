# Modelo de auditoría

## ENT-027–034

| Entidad | Responsabilidad | Invariantes principales |
|---|---|---|
| `AuditPlan` | Planificación aprobable | código único por organización; fechas coherentes; auditor activo |
| `Checklist` | Identidad estable de lista | código único; ciclo de desactivación trazable |
| `ChecklistVersion` | Contenido versionado | número único; vigencia; SHA-256; autor distinto del aprobador |
| `ChecklistItem` | Criterio ordenado | posición única; texto y tipo de respuesta obligatorios |
| `AuditExecution` | Aplicación de una lista a un plan | misma organización; plan aprobado; lista vigente |
| `AuditResponse` | Resultado por criterio | combinación ejecución–criterio única; actor y fecha |
| `Finding` | Desviación u oportunidad | origen, criterio, condición, impacto, responsable y evidencia/justificación |
| `FindingEvidence` | Vínculo a archivo | archivo sintético limpio; descripción; vínculo único |

## Integridad

- Las claves foráneas usan `PROTECT`; la historia no se elimina.
- Los gestores bloquean `QuerySet.update()` y `delete()` para evitar cambios fuera de servicios.
- Las transiciones críticas utilizan transacciones y bloqueo de filas.
- La finalización de la ejecución no modifica ni cierra sus hallazgos.
- La migración crea constraints de fechas, estados, posiciones, códigos y vínculos únicos.

## Extensiones justificadas

P12 añade metadatos de envío, aprobación y decisión a planes, listas y ejecuciones para demostrar segregación. `Finding.evidence_absence_reason` materializa RN-014 sin fabricar archivos; `audit_response_id` conserva el origen exacto del hallazgo.
