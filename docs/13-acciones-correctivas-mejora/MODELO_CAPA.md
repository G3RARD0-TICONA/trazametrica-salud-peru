# Modelo CAPA

## ENT-035–038

| Entidad | Responsabilidad | Invariantes principales |
|---|---|---|
| `RootCauseAnalysis` | Análisis causal único por hallazgo | método, análisis, conclusión y aprobación segregada |
| `CorrectiveAction` | Plan y ejecución de la tarea | causa y hallazgo coherentes; responsable, fecha y criterio obligatorios |
| `ActionEvidence` | Evidencia de ejecución | archivo sintético limpio, SHA-256 y descripción |
| `EffectivenessReview` | Decisión independiente | revisor, fecha, notas, resultado y reapertura coherente |

## Integridad

- Todas las claves foráneas usan `PROTECT` y los registros no se eliminan.
- Los gestores bloquean `QuerySet.update()` y `delete()` fuera de servicios.
- Las transiciones críticas usan transacciones y bloqueo de filas.
- Una acción conserva causa, hallazgo, autor, aprobador, ejecutor y revisor.
- El código de acción es único sin distinguir mayúsculas dentro del hallazgo.
- La ampliación de estados de `Finding` se realiza en una migración separada de P12.

## Extensiones justificadas

`CorrectiveAction.root_cause`, `is_mandatory`, metadatos de envío/aprobación y `completed_by` materializan RN-015, RN-018 y RN-019 sin crear entidades adicionales. La bitácora conserva la reasignación y las transiciones sin convertir la fila en historial editable.
