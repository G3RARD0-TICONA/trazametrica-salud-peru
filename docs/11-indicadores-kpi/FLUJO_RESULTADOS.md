# Flujo de resultados y correcciones

## Ficha KPI

```text
borrador → en revisión → aprobada/vigente
                  └────→ rechazo → borrador
vigente → sustituida/anulada
```

El autor no aprueba su ficha. La aprobación fija vigencia, fórmula, meta, umbral y hash; una nueva ficha cierra la anterior sin superponer periodos.

## Resultado

```text
calculado → en revisión → publicado
                     └→ rechazado
publicado ← nueva corrección ── publicado
    └──────────────────────────→ corregido
```

El cálculo fija entradas y posiciones antes de revisión. El calculador no publica ni rechaza su propio resultado. Un resultado corregido conserva valor y evidencia; el nuevo resultado enlaza `supersedes` y se convierte en la publicación vigente para el mismo ámbito y periodo.

## Estado de desempeño RN-013

| Sentido | En meta | Advertencia | Fuera de meta |
|---|---|---|---|
| Mayor es mejor | valor ≥ meta | umbral ≤ valor < meta | valor < umbral |
| Menor es mejor | valor ≤ meta | meta < valor ≤ umbral | valor > umbral |
| Objetivo exacto | valor = meta | diferencia ≤ tolerancia | diferencia > tolerancia |

Sin meta, el estado es `not_evaluated`. El estado se deriva; no se edita manualmente.
