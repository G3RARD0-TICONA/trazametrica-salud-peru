# P16 — Estadística y analítica avanzada

**Estado:** en revisión

**Puerta:** G16 abierta — 11/12 controles conformes

**Versión:** 1.0

**Fecha de corte:** 29 de agosto de 2026

## Objetivo

Implementar RF-036–038, CU-21, RN-027–030 y ENT-051–052 mediante análisis estadístico reproducible, definiciones versionadas, separación cronológica de entrenamiento/prueba y resultados auditables sobre observaciones exclusivamente sintéticas.

## Alcance implementado

- descriptivos, cuartiles, dispersión y detección de atípicos por regla de Tukey;
- Pareto administrativo por servicio;
- gráficos de control con línea central y límites de tres sigmas;
- tendencias, medias móviles y pronóstico ingenuo de un paso;
- regresión lineal con MAE, RMSE, R² y comparación contra la media de entrenamiento;
- regresión logística binaria con exactitud, precisión, sensibilidad, F1, Brier y matriz de confusión;
- separación cronológica entrenamiento/prueba sin barajar observaciones;
- definiciones publicadas inmutables, parámetros canónicos y SHA-256;
- ejecuciones inmutables con entradas, métricas, supuestos, resultado y hashes;
- puerta de calidad frente a línea base y registro explícito del rechazo;
- interfaz web protegida y semilla determinista de seis definiciones.

## Límites

P16 no toma decisiones clínicas, no procesa datos reales, no prescribe acciones sanitarias y no acredita validez externa. Los modelos son demostrativos y administrativos. P17 conserva las pruebas globales de seguridad, rendimiento y accesibilidad; P18 conserva el despliegue y la publicación final.

## Expediente

- [Estadística descriptiva y control](ANALISIS_ESTADISTICO.md)
- [Modelos predictivos](MODELOS_PREDICTIVOS.md)
- [Calidad, supuestos y sesgo](CALIDAD_SUPUESTOS.md)
- [Semilla demostrativa](SEMILLA_DEMO.md)
- [Trazabilidad y puerta G16](TRAZABILIDAD_G16.md)

## Resultado actual

La implementación y su expediente están listos para CI y revisión del titular. G16 conserva pendiente únicamente la aceptación formal; no se declara aprobada ni cerrada antes de esa autorización.

