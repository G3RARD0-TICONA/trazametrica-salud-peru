# P07 — Maestros organizacionales y catálogos

**Estado:** en pruebas  
**Puerta:** G07 abierta — 10/12 controles conformes; CI y aprobación pendientes  
**Versión:** 0.1  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Implementar las entidades ENT-004–ENT-008 aprobadas en P05 y cumplir RF-004/RF-005: organización, sedes, servicios, áreas y asignaciones de responsabilidad con códigos por ámbito, autoría, vigencia, desactivación controlada y ausencia de borrado físico.

## 2. Alcance implementado

- Una organización activa por instalación, protegida también por PostgreSQL.
- Sedes únicas dentro de la organización.
- Servicios únicos dentro de cada sede.
- Áreas jerárquicas sin autorreferencia ni ciclos permitidos por servicio.
- Cuatro tipos explícitos de responsabilidad y vigencias no superpuestas.
- Códigos normalizados en mayúsculas y unicidad sin distinguir mayúsculas/minúsculas.
- Campos de creación, modificación y desactivación con actor y motivo.
- Bloqueo de `delete()` tanto por instancia como por queryset.
- Servicios transaccionales que verifican `organizations.manage` antes de mutar.
- Selector y vista de consulta protegida por `organizations.view`.
- Semilla determinista e idempotente con 1 organización, 3 sedes, 20 servicios y 12 áreas ficticias.

## 3. Límites

- No existe multitenencia: solo una organización activa por instalación.
- P07 no implementa procesos, documentos, indicadores, auditorías ni datos clínicos.
- Las responsabilidades son organizacionales; los permisos por objeto se ampliarán cuando exista el módulo funcional correspondiente.
- No se permite cargar catálogos desde archivos externos ni usar nombres de clínicas reales.
- No se autoriza despliegue productivo o uso institucional.

## 4. Expediente

- [Modelo de maestros](MODELO_MAESTROS.md)
- [Reglas y servicios](REGLAS_SERVICIOS.md)
- [Semilla sintética](SEMILLA_DEMO.md)
- [Trazabilidad, pruebas y puerta G07](TRAZABILIDAD_G07.md)

## 5. Resultado provisional

El incremento está preparado para CI en Python 3.13.15 y PostgreSQL 17.11. G07 seguirá abierta hasta que GitHub Actions verifique migración, pruebas, cobertura y seguridad, y el titular acepte formalmente el resultado.
