# Flujo de versiones

## 1. Estados

```text
borrador ── enviar ──> en revisión ── aprobar ──> aprobado (vigencia futura)
   ^                         │                           │
   └──── rechazar + motivo ──┘                           └──> vigente

vigente ── nueva versión aplicable ──> sustituido
aprobado/vigente ── anular + motivo ──> anulado
```

## 2. Transiciones autorizadas

| Operación | Estado inicial | Capacidad | Resultado |
|---|---|---|---|
| Crear/editar | — / borrador | `documents.manage` | Borrador numerado y con hash |
| Enviar | Borrador | `documents.manage` | En revisión e inmutable |
| Rechazar | En revisión | `documents.review` | Regresa a borrador con motivo |
| Aprobar | En revisión | `documents.approve` | Aprobado o vigente |
| Anular | Aprobado/vigente | `documents.approve` | Anulado con motivo |
| Desactivar maestro | Sin versiones abiertas | `documents.manage` | Inactivo con evidencia |

## 3. Vigencias

Los intervalos son inclusivos. Una nueva versión no puede superponerse con otra aprobada o vigente. Si comienza después de una versión vigente, el servicio finaliza la anterior el día previo. Cuando el inicio es futuro, la anterior permanece vigente hasta su fecha final y la nueva permanece aprobada; cuando el inicio es actual, la anterior queda sustituida.

## 4. Reglas negativas

- No aprobar un borrador ni una versión ya decidida.
- No aprobar la versión propia.
- No rechazar o anular sin motivo.
- No cambiar contenido después del envío.
- No desactivar mientras existan borradores, revisiones o versiones aprobadas/vigentes.
- No reutilizar códigos ni borrar historial.

## 5. Atomicidad

Cada servicio ejecuta validación, bloqueo de filas, transición y evento de auditoría dentro de una transacción. Un error revierte la mutación completa. La bitácora actual registra operaciones confirmadas; el registro persistente de intentos denegados se incorporará con una frontera transaccional de seguridad en P17.

