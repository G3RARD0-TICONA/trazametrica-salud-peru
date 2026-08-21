# P13 — Acciones correctivas, evidencias y mejora

**Estado:** en pruebas  
**Puerta:** G13 abierta — 10/12 controles conformes  
**Versión:** 0.9  
**Fecha de corte:** 21 de agosto de 2026

## 1. Objetivo

Implementar RF-022–024, CU-12–15, RN-015–019, RNF-004 y ENT-035–038: análisis causal aprobable, acciones correctivas, responsables, vencimientos, evidencia sintética, revisión independiente de eficacia, reapertura y cierre condicionado del hallazgo.

## 2. Alcance implementado

- Análisis de causa raíz mediante cinco porqués, Ishikawa, Pareto u otro método documentado.
- Flujo de elaboración, revisión, rechazo y aprobación con autor y aprobador distintos.
- Acción correctiva vinculada a la causa aprobada y al hallazgo exacto.
- Código, tarea, responsable, vencimiento, obligatoriedad y criterio de eficacia.
- Aprobación segregada antes de ejecutar la acción.
- Reasignación motivada cuando el responsable se desactiva, sin perder historial.
- Evidencia mediante `FileAsset` sintético, limpio, descrito y trazable por SHA-256.
- Envío a verificación únicamente después de adjuntar evidencia.
- Revisión de eficacia por actor distinto del responsable y ejecutor.
- Cierre del hallazgo solo cuando todas las acciones obligatorias resultan eficaces.
- Reapertura automática de acción y hallazgo ante resultado no eficaz.
- Alertas de vencimiento, proximidad y responsable inactivo.
- Catálogo web protegido y semilla determinista de mejora.

## 3. Límites

- P13 no registra ni evalúa riesgos; corresponde a P14.
- El método causal demuestra trazabilidad interna y no garantiza por sí mismo una causa verdadera.
- La evidencia es exclusivamente sintética; no se almacenan datos clínicos ni personales reales.
- El cierre es una decisión interna del flujo demostrativo, no una certificación sanitaria, ISO o JCI.
- No se autoriza uso productivo.

## 4. Expediente

- [Modelo CAPA](MODELO_CAPA.md)
- [Flujo de mejora](FLUJO_MEJORA.md)
- [Eficacia y evidencia](EFICACIA_EVIDENCIA.md)
- [Semilla sintética](SEMILLA_DEMO.md)
- [Trazabilidad, pruebas y puerta G13](TRAZABILIDAD_G13.md)

## 5. Resultado actual

Las verificaciones locales aprobaron 124 pruebas aplicables con 83 % de cobertura, documentación, lint, tipado, modelos y migraciones conformes. G13 conserva dos pendientes: ejecución íntegra en CI con PostgreSQL 17 y aceptación formal del titular.
