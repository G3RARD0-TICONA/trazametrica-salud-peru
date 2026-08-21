# Semilla sintética P12

## Ejecución

```bash
python src/manage.py seed_audits_demo --actor admin_demo --dataset-version 1
```

Debe ejecutarse después de `seed_organizations_demo`.

## Resultado

| Objeto | Cantidad |
|---|---:|
| Planes de auditoría | 12 |
| Listas / versiones vigentes | 3 / 3 |
| Criterios | 45 |
| Ejecuciones | 12 |
| Respuestas | 180 |
| Hallazgos | 180 |
| Evidencias de archivo | 12 |

Los 168 hallazgos restantes conservan una justificación sintética de ausencia de archivo. Esto prueba RN-014 sin crear archivos innecesarios ni afirmar que la justificación sería suficiente en una auditoría real.

Los UUID y fechas se derivan de un namespace fijo. La repetición con versión 1 es idempotente y no duplica filas.
