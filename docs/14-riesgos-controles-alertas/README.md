# P14 — Riesgos, controles y alertas

**Estado:** en pruebas
**Puerta:** G14 abierta — 11/12 controles conformes antes de la aceptación
**Versión:** 0.9
**Fecha de corte:** 21 de agosto de 2026

## 1. Objetivo

Implementar RF-033–035, CU-20, RN-025–026, RNF-004 y ENT-039–043 con sus extensiones aprobables: riesgos vinculados al proceso, evaluación inherente y residual versionada, controles versionados, revisión independiente, relaciones trazables y alertas derivadas.

## 2. Alcance implementado

- Riesgo con organización, proceso, causa, evento, consecuencia, responsable y estado.
- Matriz aprobable de probabilidad e impacto de 1 a 5.
- Nivel inherente y residual calculados; el resultado no se edita manualmente.
- Evaluaciones versionadas con envío, aprobación independiente y sustitución histórica.
- Fecha explícita de próxima revisión para generar alertas reproducibles.
- Control raíz estable y versiones con tipo, frecuencia, vigencia y aprobación segregada.
- Vínculo riesgo–control con eficacia esperada y periodo de aplicación.
- Revisión independiente con resultado, notas y siguiente fecha.
- Relaciones explícitas con indicadores, hallazgos y acciones correctivas.
- Aceptación residual, cierre condicionado y reapertura motivada.
- Catálogo web protegido y semilla determinista exclusivamente sintética.

## 3. Límites

- P14 no exporta Excel, CSV, PDF ni conjuntos Power BI; corresponde a P15.
- No realiza regresión, predicción o analítica avanzada; corresponde a P16.
- La clasificación expresa prioridad administrativa interna, no riesgo clínico del paciente.
- Ningún resultado equivale a certificación, acreditación o autorización sanitaria.
- No se usan pacientes, historias clínicas, diagnósticos ni datos personales reales.
- No se autoriza uso productivo.

## 4. Expediente

- [Modelo de riesgos y controles](MODELO_RIESGOS_CONTROLES.md)
- [Matriz de evaluación](MATRIZ_EVALUACION.md)
- [Flujo de tratamiento](FLUJO_TRATAMIENTO.md)
- [Alertas y revisión](ALERTAS_REVISION.md)
- [Semilla sintética](SEMILLA_DEMO.md)
- [Trazabilidad, pruebas y puerta G14](TRAZABILIDAD_G14.md)

## 5. Resultado actual

El módulo, la migración, la semilla, la interfaz y las pruebas P14 están preparados. La CI #61 aprobó 140 pruebas sobre PostgreSQL 17, mantuvo 82 % de cobertura y dejó conformes documentación, lint, tipado, migraciones, seguridad, dependencias y construcción del contenedor. Solo permanece pendiente la aceptación formal del titular.
