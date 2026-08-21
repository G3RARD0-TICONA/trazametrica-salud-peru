# P12 — Auditorías, hallazgos y no conformidades

**Estado:** aprobada internamente  
**Puerta:** G12 cerrada — 12/12 controles conformes  
**Versión:** 1.0  
**Fecha de corte:** 21 de agosto de 2026

## 1. Objetivo

Implementar RF-019–021, CU-10–11, RN-014, RNF-004 y ENT-027–034: planes de auditoría, listas versionadas, ejecución por criterio, respuestas trazables, hallazgos/no conformidades, responsables, fechas y evidencia sintética.

## 2. Alcance implementado

- Planes con organización, código, alcance, criterios, auditor líder, fechas y estado.
- Envío, rechazo y aprobación de planes con separación entre autor y aprobador.
- Catálogo estable de listas de verificación y versiones inmutables por SHA-256.
- Criterios ordenados, obligatorios y con tipo de respuesta explícito.
- Ejecución únicamente con plan aprobado y lista vigente de la misma organización.
- Una respuesta por criterio, actor y fecha; justificación obligatoria cuando corresponde.
- Hallazgos de tipo observación, oportunidad o no conformidad.
- Clasificación de impacto, responsable activo, vencimiento y vínculo a respuesta.
- Evidencia mediante `FileAsset` limpio y sintético, o justificación expresa de ausencia.
- Envío de ejecución bloqueado si falta una respuesta obligatoria o un hallazgo para una no conformidad.
- Revisión y término de ejecución por actor distinto del auditor líder.
- Alertas derivadas de vencimiento y catálogo web protegido.
- Semilla determinista de 12 planes, 3 listas, 180 respuestas y 180 hallazgos.

## 3. Límites

- P12 no analiza causa raíz, no crea acciones correctivas y no evalúa eficacia; corresponde a P13.
- Un hallazgo abierto no puede presentarse como cerrado por el solo hecho de concluir la auditoría.
- Las listas son referencias internas configurables; no acreditan MINSA, SUSALUD, ISO o JCI.
- Los archivos de evidencia deben ser sintéticos, permitidos y validados.
- No se gestionan historias clínicas, pacientes ni resultados asistenciales reales.
- No se autoriza uso productivo.

## 4. Expediente

- [Modelo de auditoría](MODELO_AUDITORIA.md)
- [Flujo y segregación](FLUJO_AUDITORIA.md)
- [Hallazgos y evidencia](HALLAZGOS_EVIDENCIA.md)
- [Semilla sintética](SEMILLA_DEMO.md)
- [Trazabilidad, pruebas y puerta G12](TRAZABILIDAD_G12.md)

## 5. Resultado actual

Las verificaciones locales aprobaron 114 pruebas aplicables con 83 % de cobertura. Los CI #52 y #53 aprobaron 115 pruebas sobre PostgreSQL 17, mantuvieron 83 % de cobertura y dejaron conformes documentación, lint, tipado, migraciones, seguridad, dependencias y construcción del contenedor. El titular aceptó formalmente P12 el 21 de agosto de 2026; G12 queda cerrada con 12/12 controles conformes.
