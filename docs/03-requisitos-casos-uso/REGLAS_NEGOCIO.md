# Reglas de negocio

| ID | Regla | Reacción obligatoria |
|---|---|---|
| RN-001 | Todo código funcional es único dentro de su ámbito y no se reutiliza tras una desactivación | Rechazar duplicado |
| RN-002 | Un registro utilizado no se elimina físicamente | Desactivar y conservar relaciones |
| RN-003 | Solo una versión aprobada puede estar vigente por objeto y periodo | Bloquear vigencias superpuestas |
| RN-004 | Una versión aprobada es inmutable | Crear nueva versión para corregir |
| RN-005 | Autor y aprobador deben ser cuentas diferentes | Denegar autoaprobación |
| RN-006 | Todo rechazo, anulación, reapertura o excepción requiere motivo | Rechazar operación sin motivo |
| RN-007 | Un archivo sin versión de plantilla reconocida no puede aceptarse | Rechazar carga |
| RN-008 | Una carga con un error bloqueante no incorpora ninguna fila funcional | Revertir transacción y emitir detalle |
| RN-009 | El hash de un archivo aceptado no puede aceptarse nuevamente en el mismo ámbito | Marcar duplicado y vincular antecedente |
| RN-010 | Las fechas futuras solo se aceptan en campos planificados | Rechazar dato incoherente |
| RN-011 | Cada resultado KPI usa una fórmula aprobada y vigente para su periodo | Impedir cálculo/publicación |
| RN-012 | Un resultado publicado no se sobrescribe | Generar corrección versionada |
| RN-013 | La meta y el sentido del KPI determinan automáticamente su estado | Calcular estado de forma reproducible |
| RN-014 | Un hallazgo requiere criterio evaluado, descripción y evidencia o justificación de ausencia | Impedir registro incompleto |
| RN-015 | Una no conformidad requiere causa antes de aprobar su plan correctivo | Mantener estado pendiente |
| RN-016 | Una acción requiere responsable y fecha antes de pasar a ejecución | Bloquear transición |
| RN-017 | Una acción vencida permanece visible aunque se desactive su responsable | Reasignar sin perder historial |
| RN-018 | El responsable de una acción no aprueba su eficacia | Solicitar aprobador diferente |
| RN-019 | Un hallazgo solo cierra cuando todas sus acciones obligatorias están cerradas y su eficacia fue evaluada | Rechazar cierre prematuro |
| RN-020 | Toda evidencia conserva hash, nombre seguro, tipo, tamaño y fecha | Rechazar archivo no permitido |
| RN-021 | Las exportaciones incluyen versión, fecha, filtros y marca `DATOS SINTÉTICOS` | Bloquear salida incompleta |
| RN-022 | La bitácora funcional no se edita ni elimina desde la interfaz ordinaria | Denegar modificación |
| RN-023 | Un usuario inactivo no inicia sesión, pero su autoría histórica permanece visible | Bloquear acceso y conservar referencias |
| RN-024 | Ningún texto o estado del sistema equivale a certificación o autorización sanitaria | Sustituir por referencia o evidencia interna |
| RN-025 | El nivel de riesgo inherente y residual se deriva de escalas aprobadas de probabilidad e impacto | Impedir edición manual del resultado derivado |
| RN-026 | Un riesgo alto o crítico no se cierra con controles vencidos o sin evaluación residual | Rechazar cierre y generar alerta |
| RN-027 | Todo análisis usa exclusivamente observaciones sintéticas provenientes de cargas procesadas | Rechazar origen no controlado |
| RN-028 | Una definición publicada y una ejecución analítica son inmutables; mismas entradas, versión y parámetros producen el mismo hash | Crear nueva versión o ejecución |
| RN-029 | Un modelo predictivo separa entrenamiento/prueba sin fuga temporal y debe igualar su línea base | Registrar rechazo de calidad |
| RN-030 | Ningún resultado analítico equivale a diagnóstico, pronóstico o decisión clínica | Bloquear interpretación clínica |

## Estados mínimos

- Versionables: `borrador → en revisión → aprobado → vigente → sustituido/anulado`.
- Importaciones: `recibida → validando → rechazada/aceptada → procesada`.
- Auditorías: `planificada → en ejecución → concluida → cerrada`.
- Hallazgos: `abierto → en análisis → con plan → en verificación → cerrado/reabierto`.
- Acciones: `pendiente → en ejecución → en verificación → eficaz/no eficaz → cerrada/reabierta`.
- Riesgos: `identificado → evaluado → en tratamiento → controlado/aceptado → cerrado/reabierto`.

Toda transición inválida debe devolver un mensaje accionable y generar evidencia de denegación cuando sea crítica.
