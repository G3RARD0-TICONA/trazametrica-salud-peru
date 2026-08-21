# Flujo de auditoría y segregación

## Plan

```text
borrador → en revisión → aprobado → en ejecución → completado
              └───────→ rechazo → borrador
```

El autor del plan no lo aprueba. La aprobación conserva actor, fecha y motivo; un plan no aprobado no inicia ejecución.

## Lista versionada

```text
borrador + criterios → en revisión → vigente
                                      └→ sustituida por una versión posterior
```

El hash incluye identidad de lista, número, posición, criterio, obligatoriedad y tipo de respuesta. Una lista enviada no admite nuevos criterios.

## Ejecución

1. El auditor inicia con plan aprobado y lista vigente.
2. Registra una respuesta por criterio.
3. Toda respuesta obligatoria debe existir.
4. Una respuesta no conforme requiere un hallazgo vigente.
5. El auditor envía la ejecución a revisión.
6. El revisor puede devolverla con motivo.
7. Un aprobador distinto del auditor líder la completa.

Completar la auditoría no cierra hallazgos. P13 deberá demostrar causa, acciones y eficacia antes del cierre.
