# Eficacia, evidencia y alertas

## Evidencia de ejecución

`ActionEvidence` reutiliza `FileAsset`. Cada vínculo requiere archivo sintético limpio, nombre seguro, tipo permitido, tamaño, SHA-256 y descripción. El servicio valida todo antes de persistir; un archivo rechazado revierte la operación completa.

## Revisión independiente

La revisión registra:

- acción y criterio de eficacia previamente definido;
- revisor e instante inequívoco;
- resultado eficaz o no eficaz;
- notas obligatorias;
- indicador de reapertura derivado del resultado.

RN-018 bloquea al responsable y al ejecutor de la acción como revisores de eficacia. Un resultado no eficaz reabre la acción y el hallazgo sin borrar evidencia ni revisiones anteriores.

## Alertas RF-023

| Alerta | Regla |
|---|---|
| `overdue` | acción abierta con fecha anterior al día de consulta |
| `upcoming` | vence hoy o dentro de siete días |
| `on_time` | faltan más de siete días |
| `unassigned` | el responsable histórico está inactivo y requiere reasignación |
| `not_applicable` | acción cerrada o cancelada |

La reasignación exige motivo y registra en bitácora el responsable anterior y el nuevo. La acción permanece visible durante todo el cambio.
