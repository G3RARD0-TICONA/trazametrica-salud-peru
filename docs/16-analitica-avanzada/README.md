# P16 — Estadística y analítica avanzada

**Estado:** aprobada internamente

**Puerta:** G16 cerrada — 12/12 controles conformes

**Versión:** 1.0

**Fecha de corte:** 30 de agosto de 2026

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

La CI #71 aprobó 163 pruebas sobre PostgreSQL 17, 82 % de cobertura, documentación, lint, tipado, migraciones, seguridad, dependencias y construcción del contenedor. El titular aceptó formalmente P16 el 30 de agosto de 2026; G16 queda cerrada con 12/12 controles conformes.

