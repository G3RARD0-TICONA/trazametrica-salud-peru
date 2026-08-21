# Flujo de mejora y segregación

## Causa raíz

```text
borrador → en revisión → aprobado
              └───────→ rechazo → borrador
```

El autor o quien envía el análisis no puede aprobarlo. RN-015 impide crear el plan correctivo mientras la causa no esté aprobada.

## Acción correctiva

```text
pendiente → en revisión → en ejecución → en verificación → cerrada
               │                             └──────────→ reabierta → en ejecución
               └────────→ rechazo → pendiente
```

1. El gestor crea la tarea con responsable, fecha y criterio de eficacia.
2. Un aprobador distinto acepta o rechaza el plan.
3. El responsable ejecuta y adjunta evidencia sintética validada.
4. El responsable envía la acción a verificación.
5. Un verificador independiente declara eficaz o no eficaz.
6. El resultado eficaz cierra la acción; el no eficaz la reabre.

## Hallazgo

```text
abierto → en análisis → con plan → en verificación → cerrado
                                      └───────────→ reabierto
```

Completar una acción no cierra automáticamente el hallazgo. RN-019 exige que todas las acciones obligatorias estén cerradas y tengan una revisión eficaz.
