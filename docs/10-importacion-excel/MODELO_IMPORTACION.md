# Modelo de importación

| Entidad | Propósito | Integridad principal |
|---|---|---|
| `ImportTemplate` | Identidad estable de la plantilla | organización, código único, destino y ciclo de vida |
| `ImportTemplateVersion` | Contrato versionado | esquema, hash, vigencia, envío y aprobación independiente |
| `ImportJob` | Intento de carga | archivo, plantilla, organización, hash, estado, conteos y relaciones de reintento/duplicado |
| `ImportRow` | Staging trazable | número de fila único, contenido normalizado, hash y validez |
| `ImportError` | Diagnóstico accionable | fila, columna, regla, severidad, mensaje y recomendación |

Todas las claves primarias son UUID y las claves foráneas usan `PROTECT`. Plantillas, versiones, cargas, filas y errores bloquean eliminación física. Las mutaciones de estado pasan por servicios transaccionales y registran eventos append-only.

## Estados

```text
recibida → validando → rechazada
                     → aceptada → procesada
recibida → duplicada
validando → fallida
```

Una carga rechazada o fallida admite un nuevo intento enlazado; nunca se modifica el intento original. Un archivo ya aceptado o procesado en la organización produce una carga `duplicada` vinculada al antecedente.

## Atomicidad

Las filas aceptables pueden conservarse en staging para diagnóstico, pero si existe un solo error bloqueante el trabajo completo termina `rechazado` y no puede promoverse. P11 consumirá exclusivamente trabajos `procesados`.
