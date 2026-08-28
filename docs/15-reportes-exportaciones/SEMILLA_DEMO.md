# Semilla demostrativa P15

Ejecutar después del bootstrap de identidad:

```bash
python src/manage.py seed_reports_demo --actor admin_demo --dataset-version 1
```

La semilla crea idempotentemente siete contratos publicados: tablero PDF/XLSX, KPI XLSX, KPI CSV para Power BI Desktop, riesgos XLSX, hallazgos PDF y acciones correctivas CSV. Sus UUID se derivan de un namespace fijo y todos los contratos usan exclusivamente esquemas sintéticos.

La semilla solo funciona en entornos `local`, `test` o `demo`. No genera ni incorpora archivos de producción.
