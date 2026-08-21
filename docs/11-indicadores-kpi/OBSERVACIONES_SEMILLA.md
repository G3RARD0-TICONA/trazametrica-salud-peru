# Observaciones y semilla sintética

## Promoción desde P10

1. La carga debe estar `processed`, sin errores y con destino `kpi_observations`.
2. El analista selecciona un indicador activo del mismo ámbito.
3. El servicio bloquea la carga y valida cantidad, sede, servicio, periodo, decimal y dimensión.
4. Cualquier error revierte toda la operación.
5. Cada observación conserva carga y fila fuente; una carga no se materializa dos veces.

P10 valida sintaxis y estructura; P11 valida relaciones y significado KPI. La separación evita que el módulo de importaciones conozca fórmulas.

## Semilla

```bash
python src/manage.py seed_indicators_demo --actor admin_demo --dataset-version 1
```

Resultado predeterminado:

| Objeto | Cantidad |
|---|---:|
| Indicadores | 200 |
| Fichas versionadas | 260 |
| Observaciones | 100 000 |
| Procesos referenciados | 100 |
| Servicios distribuidos | 20 |

Los UUID, periodos, valores y relaciones se derivan de un namespace y fecha de corte fijos. La ejecución repetida con la misma cantidad es idempotente; una semilla parcial se bloquea para exigir restablecimiento controlado.

Para pruebas rápidas puede utilizarse `--observation-count`, entre 1 y 100 000. Esta opción no cambia el contrato del conjunto completo de referencia.

La generación local completa produjo 100 000 observaciones en 10,2 segundos sobre SQLite temporal. Este dato comprueba el generador, pero no sustituye la validación oficial con PostgreSQL 17 ni constituye la meta RNF-006.
