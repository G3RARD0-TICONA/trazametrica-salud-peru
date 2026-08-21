# Semilla y rendimiento

## Plantillas sintéticas

```bash
docker compose exec web python src/manage.py seed_import_templates_demo \
  --actor admin_demo --dataset-version 1
```

El comando requiere la organización P07 y crea de forma idempotente:

| Código | Destino |
|---|---|
| `IMP-KPI` | observaciones KPI |
| `IMP-AUD` | hallazgos de auditoría |
| `IMP-CAP` | acciones correctivas |
| `IMP-RIE` | riesgos |

Las cuatro versiones son vigentes, sus UUID son deterministas y un aprobador sintético distinto conserva la segregación. Ningún catálogo proviene de una clínica real.

## Volumen de referencia

La prueba automatizada genera desde cero un XLSX de 10 000 filas, conserva la marca sintética, lo analiza, valida y registra mediante lotes. El criterio RNF-007 exige completar en un máximo de 60 segundos; CI volverá a medirlo en PostgreSQL 17.
