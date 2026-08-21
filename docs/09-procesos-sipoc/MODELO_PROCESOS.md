# Modelo de procesos

## Entidades

| Entidad | Propósito | Integridad principal |
|---|---|---|
| `Process` | Identidad estable del proceso | organización, área activa, código único sin distinguir mayúsculas, tipo y ciclo de vida |
| `ProcessVersion` | Ficha histórica | número consecutivo, objetivo, alcance, hash, estado, vigencia y decisiones |
| `SipocEntry` | Elemento ordenado de una sección SIPOC | versión, tipo, posición, nombre y descripción |
| `Document.process` | Relación documental | opcional, misma organización y `PROTECT` |

`Process` y `ProcessVersion` no admiten eliminación física ni actualización masiva. Los cambios pasan por servicios de aplicación, transacciones y bitácora. `SipocEntry` puede eliminarse solamente dentro de un borrador y con motivo registrado.

## Tipos de proceso

- Estratégico: dirección, gobierno y planeamiento.
- Operativo: transformación principal del servicio administrativo demostrado.
- Soporte: recursos y capacidades transversales.

La clasificación organiza el catálogo; no implica jerarquía clínica ni acreditación.

## Reglas de identidad y vigencia

1. El código se normaliza a mayúsculas y es único dentro de la organización.
2. Un código desactivado no se reutiliza porque el registro se conserva.
3. Las versiones se numeran desde 1 sin sobrescribir historia.
4. No se permiten periodos aprobados superpuestos.
5. Una nueva versión efectiva trunca y sustituye la anterior cuando corresponde.
6. La ficha enviada o aprobada no permite modificar contenido ni hash.
