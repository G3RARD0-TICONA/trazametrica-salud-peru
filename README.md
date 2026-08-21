# Trazamétrica Salud Perú

Proyecto demostrativo de investigación aplicada para gestionar procesos, calidad, indicadores y analítica administrativa en clínicas privadas del Perú.

> [!IMPORTANT]
> Las Partes 0–8 tienen sus puertas cerradas. P09 es el cuarto incremento ejecutable y está listo para aceptación; G09 permanece abierta hasta la decisión formal del titular.

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
| P09 | Procesos, SIPOC y fichas | Lista para aceptación | G09 abierta (11/12) |
| P10–P18 | Datos, calidad, analítica y publicación | No iniciadas | Pendientes |

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

La arquitectura y las versiones fueron fijadas en P04 y el modelo de datos en P05. P06 implementa el primer esqueleto ejecutable; P07 añade la estructura organizacional; P08 implementa el dominio documental y P09 incorpora procesos versionados, fichas SIPOC y su vínculo documental.

## Ejecución local

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python src/manage.py migrate --noinput
docker compose exec web python src/manage.py bootstrap_access
docker compose exec web python src/manage.py seed_organizations_demo --actor admin_demo
docker compose exec web python src/manage.py seed_processes_demo --actor admin_demo
```

Antes del bootstrap, define en `.env` una contraseña sintética de al menos 12 caracteres. Consulta las guías de [identidad](docs/06-identidad-acceso/EJECUCION.md), [semilla organizacional](docs/07-maestros-organizacionales/SEMILLA_DEMO.md), [gestión documental](docs/08-gestion-documental/README.md) y [procesos/SIPOC](docs/09-procesos-sipoc/README.md). Los catálogos protegidos quedan disponibles en `/documents/` y `/processes/` con sus respectivas capacidades de consulta.

## Derechos de autor

Este repositorio no ofrece una licencia de software. Consulta [NOTICE.md](NOTICE.md) antes de usar cualquier contenido.

© 2026 Gerardo Rodney Ticona Moscoso. Todos los derechos reservados.
