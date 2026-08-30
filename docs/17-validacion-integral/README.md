# P17 — Pruebas, seguridad, rendimiento y accesibilidad

**Estado:** en pruebas

**Puerta:** G17 abierta — 11/12 controles conformes; aceptación pendiente

**Versión:** 1.0

**Fecha de corte:** 30 de agosto de 2026

## Objetivo

Validar transversalmente el sistema construido en P06–P16 contra RNF-001–013, endurecer los controles demostrativos y dejar evidencia reproducible de pruebas, seguridad, rendimiento, accesibilidad y recuperación antes del despliegue de P18.

## Alcance implementado

- regresión unitaria, integración, aceptación y sistema sobre PostgreSQL 17;
- cobertura mínima global de 80 % y caminos negativos de reglas críticas;
- Argon2 como hasher preferido, sesiones seguras y configuración demo endurecida;
- CSP, política de permisos, protección de caché y correlación de solicitudes;
- bitácora persistente de accesos autenticados denegados sin registrar consultas ni cuerpos;
- puerta de repositorio contra secretos, datos reales, binarios y artefactos prohibidos;
- `check --deploy`, Bandit, auditoría de dependencias y construcción de imagen;
- conjunto sintético de referencia con 3 sedes, 20 servicios, 100 procesos, 200 indicadores y 100 000 observaciones;
- p95 de flujos ordinarios ≤2 s, presupuesto máximo de 20 consultas y carga XLSX de 10 000 filas ≤60 s;
- revisión estructural automática y lista manual WCAG 2.2 AA de los flujos primarios;
- manifiesto reproducible para comparar la integridad antes y después de una restauración.

## Límites

P17 no publica el sistema, no selecciona proveedor o dominio, no configura un proxy real y no convierte el prototipo en una solución clínica o productiva. El almacenamiento privado definitivo, el análisis antimalware operativo, el simulacro sobre la infraestructura publicada, los manuales y la publicación final corresponden a P18.

## Expediente

- [Plan integral de pruebas](PLAN_PRUEBAS.md)
- [Seguridad y endurecimiento](SEGURIDAD.md)
- [Rendimiento de referencia](RENDIMIENTO.md)
- [Accesibilidad WCAG 2.2 AA](ACCESIBILIDAD.md)
- [Recuperación e integridad](RECUPERACION.md)
- [Trazabilidad y puerta G17](TRAZABILIDAD_G17.md)

## Resultado actual

La CI #75 aprobó 170 pruebas sobre PostgreSQL 17, 82 % de cobertura, documentación, lint, tipado, migraciones, seguridad del repositorio, `check --deploy`, accesibilidad, rendimiento, Bandit, dependencias y construcción del contenedor. G17 conserva pendiente únicamente la aceptación formal del titular.
