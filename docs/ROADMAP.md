# Roadmap modular

El roadmap controla el orden del proyecto; no sustituye los criterios de aceptación de cada expediente.

| Parte | Resultado esperado | Estado actual |
|---|---|---|
| P00 | Definición, alcance y gobierno | Aprobada internamente |
| P01 | Demanda laboral y perfiles objetivo | Aprobada internamente |
| P02 | Matriz legal, normativa y de referencias | Aprobada internamente |
| P03 | Requisitos, actores y casos de uso | Aprobada internamente |
| P04 | Arquitectura, entornos y decisiones técnicas | Aprobada internamente |
| P05 | Modelo de datos y diccionario | Aprobada internamente |
| P06 | Identidad, autenticación, roles y permisos | Aprobada internamente |
| P07 | Maestros organizacionales y catálogos | Aprobada internamente — G07 cerrada (12/12) |
| P08 | Gestión documental y control de versiones | Aprobada internamente — G08 cerrada (12/12) |
| P09 | Procesos, SIPOC y fichas | Aprobada internamente — G09 cerrada (12/12) |
| P10 | Importación Excel y calidad de datos | Aprobada internamente — G10 cerrada (12/12) |
| P11 | Catálogo, cálculo y seguimiento de KPI | Aprobada internamente — G11 cerrada (12/12) |
| P12 | Auditorías, hallazgos y no conformidades | Aprobada internamente — G12 cerrada (12/12) |
| P13 | Acciones correctivas, evidencias y mejora | Aprobada internamente — G13 cerrada (12/12) |
| P14 | Riesgos, alertas y controles | Aprobada internamente — G14 cerrada (12/12) |
| P15 | Exportaciones, Power BI Desktop y reportes | Aprobada internamente — G15 cerrada (12/12) |
| P16 | Analítica estadística y capacidades avanzadas | Aprobada internamente — G16 cerrada (12/12) |
| P17 | Pruebas, seguridad, rendimiento y accesibilidad | En pruebas — G17 abierta (11/12) |
| P18 | Despliegue demostrativo, documentación y publicación | No iniciada |

## Regla de avance

1. Investigar fuentes, usuarios, datos, riesgos y dependencias.
2. Definir reglas, permisos, alertas, cálculos y pruebas de aceptación.
3. Elaborar el expediente y evaluar su puerta.
4. Implementar únicamente requisitos aprobados.
5. Integrar, probar y registrar evidencia antes de cerrar la parte.

P04–P16 están aprobadas internamente. P11 materializa fichas KPI versionadas, fórmulas declarativas, observaciones, cálculo reproducible y publicación corregible; superó las verificaciones locales, los CI #48, #49 y #50 sobre PostgreSQL 17 y la aceptación formal del titular. G11 queda cerrada con 12/12 controles conformes.

P12 materializa planes, listas versionadas, respuestas, hallazgos/no conformidades y evidencia sintética. Superó las verificaciones locales, los CI #52 y #53 sobre PostgreSQL 17 con 115 pruebas y 83 % de cobertura, y la aceptación formal del titular del 21 de agosto de 2026. G12 queda cerrada con 12/12 controles conformes.

P13 materializa causa raíz, acciones correctivas, evidencia de ejecución, alertas y revisión independiente de eficacia. Superó las verificaciones locales y las CI #56 y #57 sobre PostgreSQL 17 con 125 pruebas y 83 % de cobertura. El titular autorizó formalmente su aprobación e integración el 21 de agosto de 2026; G13 queda cerrada con 12/12 controles conformes.

P14 materializa riesgos por proceso, matriz inherente y residual, controles versionados, relaciones explícitas con KPI, hallazgos y acciones, revisión independiente, alertas y cierre condicionado. Las CI #61 y #62 aprobaron 140 pruebas sobre PostgreSQL 17 con 82 % de cobertura. El titular autorizó expresamente el cierre el 28 de agosto de 2026; G14 queda cerrada con 12/12 controles conformes.

P15 materializa tablero filtrable, contratos de exportación versionados, archivos CSV/XLSX/PDF auditables y un conjunto estable para Power BI Desktop. Las CI #67 y #68 aprobaron 151 pruebas sobre PostgreSQL 17 con 82 % de cobertura, seguridad y dependencias conformes. El titular autorizó formalmente su aprobación e integración el 29 de agosto de 2026; G15 queda cerrada con 12/12 controles conformes.

P16 materializa estadística descriptiva, Pareto, gráficos de control, tendencias, regresión lineal y logística mediante definiciones y ejecuciones versionadas. La CI #71 aprobó 163 pruebas sobre PostgreSQL 17 con 82 % de cobertura, seguridad, dependencias e imagen conformes. El titular autorizó formalmente su aprobación e integración el 30 de agosto de 2026; G16 queda cerrada con 12/12 controles conformes.

P17 valida regresión integral, seguridad transversal, rendimiento con el conjunto sintético de referencia, accesibilidad WCAG 2.2 AA y recuperación mediante manifiesto. La CI #75 aprobó 170 pruebas sobre PostgreSQL 17 con 82 % de cobertura y dejó conformes seguridad, dependencias, accesibilidad, rendimiento e imagen. G17 queda en 11/12; falta la aceptación formal del titular.
