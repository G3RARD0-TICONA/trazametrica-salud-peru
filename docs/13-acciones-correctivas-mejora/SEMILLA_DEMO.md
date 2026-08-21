# Semilla sintética P13

## Ejecución

```bash
python src/manage.py seed_improvements_demo --actor admin_demo --dataset-version 1
```

Debe ejecutarse después de `seed_organizations_demo` y `seed_audits_demo`.

## Resultado

| Objeto | Cantidad |
|---|---:|
| Análisis de causa aprobados | 12 |
| Acciones correctivas | 24 |
| Evidencias de acción | 18 |
| Revisiones de eficacia | 15 |
| Acciones cerradas eficaces | 12 |
| Hallazgos cerrados | 6 |
| Acciones reabiertas no eficaces | 3 |
| Acciones en verificación | 3 |

Los UUID, estados y fechas se derivan de un namespace y corte fijos. La repetición con versión 1 es idempotente y no duplica filas. Los escenarios abiertos, reabiertos y cerrados permiten demostrar alertas y RN-019 sin afirmar resultados clínicos reales.
