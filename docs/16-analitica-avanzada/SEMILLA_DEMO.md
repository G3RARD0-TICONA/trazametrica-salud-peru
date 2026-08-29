# Semilla demostrativa P16

Ejecutar después de P11:

```bash
python src/manage.py seed_analytics_demo --actor admin_demo --dataset-version 1
```

La semilla crea idempotentemente seis definiciones publicadas: descriptivos, Pareto, gráfico de control, media móvil, regresión lineal y regresión logística. Cada definición utiliza un KPI sintético con observaciones originadas en una carga P11 procesada.

La primera ejecución de cada definición conserva métricas, supuestos, hashes y estado de calidad. Repetir la semilla no duplica definiciones ni ejecuciones. El comando solo funciona en `local`, `test` o `demo` y nunca incorpora información real.

