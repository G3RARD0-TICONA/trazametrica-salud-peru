# P15 — Reportes, Excel, PDF y Power BI Desktop

**Estado:** aprobada internamente

**Puerta:** G15 cerrada — 12/12 controles conformes

**Versión:** 1.0

**Fecha de corte:** 28 de agosto de 2026

## Objetivo

Implementar RF-028–030, CU-16, RN-021, RNF-014 y ENT-044–045 mediante un tablero KPI filtrable, contratos de exportación versionados, salidas CSV/XLSX/PDF auditables y un conjunto estable para Power BI Desktop.

## Alcance implementado

- filtros por periodo, sede, servicio, proceso, indicador y estado;
- contratos con versión, esquema ordenado y hash SHA-256;
- publicación y sustitución histórica sin sobrescribir contratos publicados;
- archivos CSV UTF-8, XLSX y PDF con marca `DATOS SINTÉTICOS`;
- neutralización de fórmulas en celdas CSV/XLSX;
- conjunto CSV estable para Power BI Desktop local;
- registro por ejecución con solicitante, filtros, filas, archivo y hash;
- permisos separados para consulta y exportación;
- semilla determinista de siete contratos publicados.

## Límites

P15 no incluye Power BI Service, publicación en la nube, regresión, predicción ni analítica avanzada. Esas capacidades quedan fuera del MVP o corresponden a P16. Los archivos son demostrativos y no contienen información clínica real.

## Expediente

- [Contratos de exportación](CONTRATOS_EXPORTACION.md)
- [Filtros del tablero](FILTROS_TABLERO.md)
- [Excel, CSV y Power BI](EXCEL_CSV_POWER_BI.md)
- [PDF y seguridad](PDF_SEGURIDAD.md)
- [Semilla demostrativa](SEMILLA_DEMO.md)
- [Trazabilidad y puerta G15](TRAZABILIDAD_G15.md)

## Resultado actual

Las CI #67 y #68 aprobaron 151 pruebas sobre PostgreSQL 17, 82 % de cobertura, documentación, lint, tipado, migraciones, seguridad, dependencias y construcción del contenedor. El titular aceptó formalmente P15 el 29 de agosto de 2026; G15 queda cerrada con 12/12 controles conformes.
