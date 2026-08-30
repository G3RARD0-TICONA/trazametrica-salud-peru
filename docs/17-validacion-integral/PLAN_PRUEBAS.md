# Plan integral de pruebas

## Estrategia

| Nivel | Objetivo | Evidencia automatizada |
|---|---|---|
| Unitaria | cálculos, matrices, validadores y adaptadores deterministas | `tests/unit` |
| Integración | ORM, restricciones, transacciones, permisos y archivos | `tests/integration` sobre PostgreSQL 17 |
| Seguridad | cabeceras, CSRF, caché, mínimo privilegio y bitácora de denegaciones | `tests/security` y puertas CI |
| Rendimiento | p95, consultas ORM, conjunto de 100 000 observaciones y XLSX de 10 000 filas | `tests/performance` y prueba P10 marcada |
| Recuperación | conteos, migraciones y manifiesto de archivos tras restauración | comando `recovery_manifest` |
| Accesibilidad | estructura HTML y revisión manual de flujos primarios | `scripts/check_accessibility.py` y checklist P17 |

## Reglas de aceptación

- todas las pruebas se ejecutan con Python 3.13 y PostgreSQL 17 en CI;
- la cobertura global de ramas y sentencias no baja de 80 %;
- un fallo de autorización, integridad, seguridad, migración o dependencia bloquea la integración;
- las pruebas no usan red externa, datos reales ni orden global compartido;
- el conjunto grande es sintético, versionado y regenerable;
- los umbrales temporales se miden con reloj monotónico y se acompañan de presupuestos de consultas para reducir falsos positivos.

## Regresión crítica

Se conservan las pruebas de segregación autor–aprobador, inmutabilidad, rollback, fórmulas declarativas, XLSX sin macros, contratos de exportación, hashes, separación temporal analítica, restricciones PostgreSQL y permisos por capacidad. P17 agrega pruebas transversales, pero no sustituye la evidencia de cada parte.
