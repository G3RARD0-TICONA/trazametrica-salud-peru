# P05 — Modelo de datos y diccionario

**Estado:** aprobada internamente  
**Puerta:** G05 cerrada — 12/12 controles conformes  
**Versión:** 1.0  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Convertir los requisitos de P03 y la arquitectura de P04 en un modelo de datos implementable sobre Django 5.2 LTS y PostgreSQL 17. P05 define entidades, relaciones, nombres físicos, tipos, restricciones, índices, historización, archivos, migraciones y semillas sintéticas sin adelantar interfaces o permisos detallados de P06.

## 2. Decisiones de datos

| Área | Decisión |
|---|---|
| Identidad | UUID nativo como clave primaria de toda tabla del dominio |
| Organización | Una organización por instalación, conservando `organization_id` en ámbitos funcionales |
| Tiempo | `timestamptz` en UTC para instantes; `date` para periodos de negocio; presentación en `America/Lima` |
| Números | `numeric`/`DecimalField` para KPI y valores exactos; nunca `float` para resultados publicados |
| Versiones | Raíz estable y tabla de versiones inmutables para procesos, documentos, KPI, listas y referencias |
| Borrado | Sin borrado físico de registros usados; desactivación explícita y relaciones protegidas |
| Archivos | Contenido fuera de PostgreSQL; la base conserva identificador, ruta opaca, hash y metadatos |
| JSON | Uso limitado a staging, filtros y contexto técnico con esquema versionado |
| Integridad | Reglas críticas duplicadas en servicio y restricciones PostgreSQL cuando sean expresables |
| Índices | Solo para unicidad, claves foráneas y consultas demostradas; revisión mediante `EXPLAIN` en P17 |
| Migraciones | Migraciones Django versionadas, pequeñas, probadas y sin editar después de integrarse |
| Semillas | Dataset sintético, determinista, idempotente, versionado y regenerable |

## 3. Base técnica oficial

- Django permite declarar [`CheckConstraint` y `UniqueConstraint`](https://docs.djangoproject.com/en/5.2/ref/models/constraints/) en el modelo y validarlas también contra la base.
- Los [índices de Django](https://docs.djangoproject.com/en/5.2/ref/models/indexes/) admiten columnas, expresiones y condiciones; su existencia deberá justificarse por consultas reales.
- PostgreSQL recomienda `numeric` cuando se requiere exactitud y documenta sus límites en [tipos numéricos](https://www.postgresql.org/docs/17/datatype-numeric.html).
- Los instantes se conservarán con zona horaria siguiendo los [tipos de fecha y hora de PostgreSQL](https://www.postgresql.org/docs/17/datatype-datetime.html).
- Las reglas relacionales usarán [restricciones PostgreSQL](https://www.postgresql.org/docs/17/ddl-constraints.html); una clave foránea no sustituye automáticamente todos los índices de consulta.
- [`jsonb`](https://www.postgresql.org/docs/17/datatype-json.html) no reemplazará el modelo relacional y solo se usará donde el esquema de entrada o contexto sea variable.

## 4. Expediente

- [Modelo de dominio y relaciones](MODELO_DOMINIO.md)
- [Diccionario físico de datos](DICCIONARIO_DATOS.md)
- [Integridad, historización e índices](REGLAS_INTEGRIDAD.md)
- [Migraciones, semillas y recuperación](MIGRACIONES_SEMILLAS.md)
- [Trazabilidad, pruebas y puerta G05](TRAZABILIDAD_G05.md)

## 5. Resultado actual

El expediente define 46 entidades físicas, sus campos comunes y específicos, relaciones, restricciones, índices previstos, reglas de conservación, dataset de referencia y 18 pruebas de aceptación de datos. El titular aceptó el modelo y aprobó internamente los 12 controles de G05 el 20 de agosto de 2026.
