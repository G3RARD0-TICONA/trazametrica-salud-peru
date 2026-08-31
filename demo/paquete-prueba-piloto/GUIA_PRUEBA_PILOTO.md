# Guía de prueba piloto — Trazamétrica Salud Perú

Este paquete contiene únicamente datos sintéticos. No incluye datos de pacientes, historias clínicas ni información real.

## 1. Preparar la demo local

Desde la carpeta `trazametrica-salud-peru`, con los contenedores ya iniciados, ejecute:

```bash
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_organizations_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_processes_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_import_templates_demo --actor admin_demo
```

Recargue `http://localhost:8080` e ingrese con `admin_demo`.

## 2. Cargar el paquete de importaciones

En el módulo **Importaciones**, seleccione la plantilla y cargue el archivo correspondiente:

| Orden | Plantilla | Archivo |
|---|---|---|
| 1 | `IMP-KPI` | `01_KPI_Observaciones_Sinteticas.xlsx` |
| 2 | `IMP-AUD` | `02_Auditoria_Hallazgos_Sinteticos.xlsx` |
| 3 | `IMP-CAP` | `03_Acciones_Correctivas_Sinteticas.xlsx` |
| 4 | `IMP-RIE` | `04_Riesgos_Sinteticos.xlsx` |

No altere las hojas `META`, los encabezados ni los códigos de plantilla. Cada archivo contiene hojas `DATOS`, `INSTRUCCIONES` y `META`.

## 3. Evidencias que se deben comprobar

- La carga se registra y conserva quién la realizó.
- Las filas muestran su estado de validación.
- Los códigos de observación, hallazgo, acción y riesgo son únicos dentro de cada archivo.
- Los tipos y rangos se validan: fechas, decimales, probabilidades e impactos de 1 a 5.
- La interfaz muestra únicamente la marca de datos sintéticos.

## 4. Prueba de rechazo controlada

Haga una copia del archivo KPI. En la copia, duplique `KPI-2026-001` en otra fila y cárguela nuevamente. El sistema debe rechazar o registrar el error de duplicidad; después puede conservar el archivo original como evidencia de una carga válida.

## 5. Recorrido ampliado de la demo

Para completar el recorrido funcional use las semillas de indicadores, auditorías, mejoras, riesgos, reportes y analítica que existen en el proyecto. El paquete Excel prueba el flujo de importación; las semillas permiten visualizar el resto de los módulos P00–P18 desde el navegador.
