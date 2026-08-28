# Alertas y revisión

## 1. Alertas derivadas

Las alertas no se almacenan como estados paralelos. Se calculan desde el estado funcional, responsable, banda, vínculos y fechas; la misma entrada y fecha de corte producen el mismo resultado.

| Alerta | Regla |
|---|---|
| `pending_assessment` | Riesgo sin evaluación aprobada |
| `treatment_required` | Riesgo alto o crítico sin control vinculado |
| `unassigned` | Responsable inactivo o control desactivado |
| `overdue` | Próxima revisión anterior a la fecha de corte |
| `upcoming` | Revisión entre hoy y siete días inclusivos |
| `pending_review` | Control aplicable sin revisión |
| `ineffective` | Última revisión del control ineficaz |
| `on_time` | Sin condición prioritaria |
| `not_applicable` | Riesgo cerrado o vínculo fuera de vigencia |

## 2. Precedencia

El cierre o fin de vigencia se evalúa primero; luego responsable, existencia de evaluación/revisión, ineficacia, vencimiento, proximidad y tratamiento. Esta precedencia evita ocultar un responsable inactivo detrás de una fecha todavía vigente.

## 3. Alcance

P14 muestra alertas dentro de la aplicación. No envía correo, SMS ni notificaciones externas, no usa tareas programadas permanentes y no introduce umbrales clínicos.
