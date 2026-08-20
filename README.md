# Trazamétrica Salud Perú

Proyecto demostrativo de investigación aplicada para gestionar procesos, calidad, indicadores y analítica administrativa en clínicas privadas del Perú.

> [!IMPORTANT]
> El proyecto se encuentra en fase de diseño. Todavía no existe una versión ejecutable. Las Partes 0, 1, 2 y 3 están aprobadas internamente.

## Propósito

Trazamétrica Salud Perú busca demostrar, mediante un sistema reproducible, la trazabilidad entre:

`fuente de datos → validación → proceso → indicador → hallazgo → acción de mejora`

El resultado final será un portafolio técnico que integre gestión por procesos, control de calidad, Excel, PostgreSQL, Python y exportaciones preparadas para Power BI Desktop.

## Alcance previsto del MVP

- Maestros de organización, sede, servicio, proceso, usuario, documento e indicador.
- Importación de plantillas Excel con validaciones y registro de errores.
- Fichas versionadas de procesos e indicadores.
- Auditorías, hallazgos, no conformidades, acciones correctivas y evidencias.
- Riesgos, controles, responsables, revisiones y alertas de vencimiento.
- Permisos por rol y bitácora de operaciones.
- Exportaciones a Excel, PDF y conjuntos limpios para Power BI Desktop.
- Datos de demostración exclusivamente sintéticos.

## Fuera de alcance

- Atención, diagnóstico o decisión clínica.
- Historias clínicas, recetas, resultados médicos o interoperabilidad con sistemas clínicos reales.
- Datos personales o de salud reales.
- Certificación, acreditación o representación de MINSA, SUSALUD, ISO, JCI, SANNA, AUNA, Grupo San Pablo u otra institución.
- Despliegue productivo en una clínica sin evaluación jurídica, de seguridad y operativa independiente.

## Estado por partes

| Parte | Tema | Estado | Puerta |
|---|---|---|---|
| P00 | Definición y gobierno | Aprobada internamente | G00 cerrada |
| P01 | Demanda laboral y perfiles objetivo | Aprobada internamente | G01 cerrada |
| P02 | Marco legal, normativo y referencias | Aprobada internamente | G02 cerrada |
| P03 | Requisitos, actores y casos de uso | Aprobada internamente | G03 cerrada |
| P04–P18 | Arquitectura, datos, construcción, pruebas y publicación | No iniciadas | Pendientes |

Consulta el [roadmap](docs/ROADMAP.md) y el [índice de documentación](docs/README.md).

## Uso seguro de datos

Este repositorio público solo admitirá datos sintéticos. No publiques nombres reales, documentos de identidad, teléfonos, correos personales, diagnósticos, historias clínicas, credenciales, tokens, archivos `.env`, exportaciones de producción ni capturas de sistemas clínicos.

Las reglas completas se encuentran en [SECURITY.md](SECURITY.md).

## Tecnología prevista

- Python y Django para la aplicación web.
- PostgreSQL como base de datos.
- Excel para plantillas de entrada y salidas controladas.
- Power BI Desktop para análisis local sobre exportaciones limpias.
- Docker Compose para un entorno reproducible de desarrollo.
- Pruebas automatizadas y CI en GitHub Actions.

La arquitectura y las versiones se fijarán en sus partes correspondientes antes de implementar dependencias.

## Derechos de autor

Este repositorio no ofrece una licencia de software. Consulta [NOTICE.md](NOTICE.md) antes de usar cualquier contenido.

© 2026 Gerardo Rodney Ticona Moscoso. Todos los derechos reservados.
