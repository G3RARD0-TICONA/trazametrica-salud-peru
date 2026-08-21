# P09 — Procesos, SIPOC y fichas

**Estado:** en pruebas  
**Puerta:** G09 abierta — 10/12 controles conformes  
**Versión:** 0.9  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Implementar RF-006, RF-007, RF-009, CU-04, CU-05, RN-001–006 y las entidades ENT-009–011: catálogo de procesos por organización y área propietaria, fichas versionadas, las cinco secciones SIPOC, aprobación independiente, vigencia, historial y vínculo trazable con documentos.

## 2. Alcance implementado

- Procesos estratégicos, operativos y de soporte con código único no reutilizable.
- Fichas versionadas con objetivo, alcance, SHA-256 y autoría.
- SIPOC ordenado por proveedor, entrada, actividad, salida y cliente.
- Validación de las cinco secciones antes de enviar a revisión.
- Flujo `borrador → en revisión → aprobado/vigente → sustituido/anulado`.
- Separación obligatoria entre autor y aprobador.
- Rechazo, anulación, desvinculación y desactivación con motivo.
- Una sola versión efectiva por periodo, sin solapamientos.
- Contenido y SIPOC inmutables después del envío.
- Vínculo opcional y protegido entre documento y proceso de la misma organización.
- Bitácora append-only para operaciones exitosas.
- Catálogo y ficha protegidos por `processes.view`.
- Semilla determinista de 100 procesos, 100 versiones y 500 elementos SIPOC sintéticos.

## 3. Límites

- Las fichas describen procesos administrativos demostrativos; no modelan atención, diagnóstico ni decisión clínica.
- Los nombres y contenidos de la semilla son ficticios y no representan procedimientos de una clínica real.
- P09 implementa consulta web; las mutaciones se ejecutan mediante servicios transaccionales hasta consolidar la interfaz transversal.
- La aprobación es interna al proyecto y no equivale a certificación, acreditación ni validación sanitaria.
- No se autoriza uso productivo.

## 4. Expediente

- [Modelo de procesos](MODELO_PROCESOS.md)
- [Flujo de versiones](FLUJO_VERSIONES.md)
- [Ficha y SIPOC](SIPOC_FICHA.md)
- [Semilla demostrativa](SEMILLA_DEMO.md)
- [Trazabilidad, pruebas y puerta G09](TRAZABILIDAD_G09.md)

## 5. Resultado actual

Las verificaciones locales aprobaron 67 pruebas aplicables con 86 % de cobertura, lint, tipado, sistema Django y migraciones reproducibles. G09 conserva dos pendientes: ejecución íntegra en CI con PostgreSQL 17 y aceptación formal del titular.
