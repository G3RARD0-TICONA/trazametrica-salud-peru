# Semilla sintética P14

## Contrato

El comando `seed_risks_demo` requiere las semillas P09, P11, P12 y P13. Solo funciona en entornos local, test o demo y rechaza versiones de dataset desconocidas.

| Objeto | Cantidad |
|---|---:|
| Riesgos | 20 |
| Evaluaciones | 24 |
| Controles | 12 |
| Versiones de control | 12 |
| Vínculos riesgo–control | 24 |
| Revisiones de control | 18 |
| Vínculos con KPI | 20 |
| Vínculos con hallazgos | 12 |
| Vínculos con acciones | 12 |

Los UUID se derivan de un espacio de nombres fijo. Repetir el comando no duplica registros y las fechas de corte permiten demostrar vencido, próximo, vigente, pendiente e ineficaz.

```bash
python src/manage.py seed_risks_demo --actor admin_demo --dataset-version 1
```

Todos los textos, cuentas y relaciones son ficticios y usan dominios reservados o marcas visibles de datos sintéticos.
