# Flujo de versiones de proceso

| Estado | Acción permitida | Siguiente estado |
|---|---|---|
| Borrador | editar ficha y SIPOC; enviar | En revisión |
| En revisión | rechazar con motivo | Borrador |
| En revisión | aprobar por actor distinto | Aprobado o vigente |
| Aprobado | esperar inicio de vigencia o anular | Vigente o anulado |
| Vigente | sustituir mediante nueva versión o anular | Sustituido o anulado |
| Sustituido | consulta histórica | terminal |
| Anulado | consulta histórica | terminal |

## Controles

- Autor y aprobador siempre son usuarios distintos.
- Solo un actor con `processes.approve` aprueba o anula.
- Rechazo y anulación exigen motivo no vacío.
- Envío exige objetivo, alcance y SIPOC completo.
- Toda versión conserva hash SHA-256 sobre ficha y SIPOC ordenado.
- La anulación no borra la versión ni sus evidencias.
- La desactivación del proceso exige cerrar versiones y desvincular documentos activos.
