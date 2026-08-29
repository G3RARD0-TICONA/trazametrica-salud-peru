# Trazamétrica Salud Perú

Proyecto demostrativo de investigación aplicada para gestionar procesos, calidad, indicadores y analítica administrativa en clínicas privadas del Perú.

> [!IMPORTANT]
> Las Partes 0–15 tienen sus puertas cerradas. P15 está aprobada internamente y G15 quedó cerrada con 12/12 controles conformes tras la aceptación formal del titular.

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
| P04 | Arquitectura, entornos y decisiones técnicas | Aprobada internamente | G04 cerrada |
| P05 | Modelo de datos y diccionario | Aprobada internamente | G05 cerrada |
| P06 | Identidad, autenticación, roles y permisos | Aprobada internamente | G06 cerrada |
| P07 | Maestros organizacionales y catálogos | Aprobada internamente | G07 cerrada (12/12) |
| P08 | Gestión documental y control de versiones | Aprobada internamente | G08 cerrada (12/12) |
| P09 | Procesos, SIPOC y fichas | Aprobada internamente | G09 cerrada (12/12) |
| P10 | Importación Excel y calidad de datos | Aprobada internamente | G10 cerrada (12/12) |
| P11 | Catálogo, cálculo y seguimiento de KPI | Aprobada internamente | G11 cerrada (12/12) |
| P12 | Auditorías, hallazgos y no conformidades | Aprobada internamente | G12 cerrada (12/12) |
| P13 | Acciones correctivas, evidencias y mejora | Aprobada internamente | G13 cerrada (12/12) |
| P14 | Riesgos, controles versionados y alertas | Aprobada internamente | G14 cerrada (12/12) |
| P15 | Reportes, Excel, PDF y Power BI Desktop | Aprobada internamente | G15 cerrada (12/12) |
| P16–P18 | Analítica, endurecimiento y publicación | No iniciadas | Pendientes |

Consulta el [roadmap](docs/ROADMAP.md) y el [índice de documentación](docs/README.md).

## Uso seguro de datos

Este repositorio público solo admitirá datos sintéticos. No publiques nombres reales, documentos de identidad, teléfonos, correos personales, diagnósticos, historias clínicas, credenciales, tokens, archivos `.env`, exportaciones de producción ni capturas de sistemas clínicos.

Las reglas completas se encuentran en [SECURITY.md](SECURITY.md).

## Tecnología prevista

- Python 3.13 y Django 5.2 LTS para la aplicación web.
- PostgreSQL 17 como base de datos única de desarrollo, pruebas y demostración.
- Excel para plantillas de entrada y salidas controladas.
- Power BI Desktop para análisis local sobre exportaciones limpias.
- Docker Compose Specification para entornos reproducibles.
- Pruebas automatizadas y CI en GitHub Actions.

La arquitectura y las versiones fueron fijadas en P04 y el modelo de datos en P05. P06 implementa identidad; P07 la estructura organizacional; P08 documentos; P09 procesos y SIPOC; P10 incorpora plantillas Excel y trazabilidad de cargas; P11 añade KPI reproducibles; P12 incorpora auditorías y hallazgos; P13 añade causa raíz, acciones correctivas y eficacia; P14 incorpora riesgos, controles versionados y alertas; P15 incorpora contratos y exportaciones auditables.

## Ejecución local

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python src/manage.py migrate --noinput
docker compose exec web python src/manage.py bootstrap_access
docker compose exec web python src/manage.py seed_organizations_demo --actor admin_demo
docker compose exec web python src/manage.py seed_processes_demo --actor admin_demo
docker compose exec web python src/manage.py seed_import_templates_demo --actor admin_demo
docker compose exec web python src/manage.py seed_indicators_demo --actor admin_demo
docker compose exec web python src/manage.py seed_audits_demo --actor admin_demo
docker compose exec web python src/manage.py seed_improvements_demo --actor admin_demo
docker compose exec web python src/manage.py seed_risks_demo --actor admin_demo
docker compose exec web python src/manage.py seed_reports_demo --actor admin_demo
```

Antes del bootstrap, define en `.env` una contraseña sintética de al menos 12 caracteres. Consulta las guías de [identidad](docs/06-identidad-acceso/EJECUCION.md), [semilla organizacional](docs/07-maestros-organizacionales/SEMILLA_DEMO.md), [gestión documental](docs/08-gestion-documental/README.md), [procesos/SIPOC](docs/09-procesos-sipoc/README.md), [importación Excel](docs/10-importacion-excel/README.md), [indicadores](docs/11-indicadores-kpi/README.md), [auditorías](docs/12-auditorias-hallazgos/README.md), [mejora](docs/13-acciones-correctivas-mejora/README.md), [riesgos](docs/14-riesgos-controles-alertas/README.md) y [reportes](docs/15-reportes-exportaciones/README.md). Los catálogos protegidos quedan disponibles en `/documents/`, `/processes/`, `/imports/`, `/indicators/`, `/audits/`, `/improvements/`, `/risks/` y `/reports/`.

## Derechos de autor

Este repositorio no ofrece una licencia de software. Consulta [NOTICE.md](NOTICE.md) antes de usar cualquier contenido.

© 2026 Gerardo Rodney Ticona Moscoso. Todos los derechos reservados.
