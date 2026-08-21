# P11 — Catálogo, cálculo y seguimiento de KPI

**Estado:** en revisión  
**Puerta:** G11 abierta — 11/12 controles conformes  
**Versión:** 0.9  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Implementar RF-015–018, CU-08–09, RN-011–013, RNF-005 y ENT-022–026: fichas KPI versionadas, fórmulas declarativas, observaciones provenientes de cargas procesadas, resultados reproducibles, estados de desempeño, aprobación independiente y correcciones sin sobrescritura.

## 2. Alcance implementado

- Catálogo estable por organización, proceso, código y responsable.
- Fichas versionadas con propósito, unidad, frecuencia, sentido, meta y umbral.
- Fórmula JSON normalizada, SHA-256 e historial inmutable después del envío.
- Motor decimal con operadores permitidos; no usa `eval`, `exec`, SQL ni código libre.
- Materialización atómica de observaciones desde una carga P10 procesada.
- Cálculo por periodo, sede, servicio y roles de entrada explícitos.
- Trazabilidad de versión, observaciones, posiciones, valor, actor y hash del resultado.
- Estado automático: en meta, advertencia, fuera de meta o sin evaluación.
- Revisión, rechazo y publicación con separación entre calculador y publicador.
- Corrección mediante un nuevo resultado; el publicado anterior conserva su valor.
- Catálogo y detalle web protegidos por autorización y marcados como sintéticos.
- Semilla determinista de 200 KPI, 260 fichas y hasta 100 000 observaciones.

## 3. Límites

- Los KPI son administrativos y demostrativos; no miden pacientes ni resultados clínicos reales.
- Las fórmulas no aceptan Python, Excel, JavaScript, SQL ni expresiones arbitrarias.
- P11 no implementa tableros ni exportaciones; corresponden a P15.
- Las alertas operativas multicanal no forman parte de P11; el estado de desempeño queda disponible para módulos posteriores.
- Una carga P10 completa se asigna a un indicador; la mezcla de varios indicadores en el mismo archivo no pertenece al contrato actual.
- Solo se admiten datos sintéticos y no se autoriza uso productivo.

## 4. Expediente

- [Modelo de indicadores](MODELO_INDICADORES.md)
- [Fórmulas seguras](FORMULAS_SEGURAS.md)
- [Observaciones y semilla](OBSERVACIONES_SEMILLA.md)
- [Flujo de resultados y correcciones](FLUJO_RESULTADOS.md)
- [Trazabilidad, pruebas y puerta G11](TRAZABILIDAD_G11.md)

## 5. Resultado actual

El CI #48 aprobó 104 pruebas sobre PostgreSQL 17 con 83 % de cobertura, documentación, lint, tipado, modelos, migraciones, seguridad, dependencias y contenedor conformes. G11 conserva un único pendiente: la aceptación formal del titular.
