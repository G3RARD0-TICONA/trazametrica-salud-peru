# P04 — Arquitectura, entornos y decisiones técnicas

**Estado:** aprobada internamente  
**Puerta:** G04 cerrada — 12/12 controles conformes  
**Versión:** 1.0  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Definir una arquitectura implementable, segura y reproducible para cumplir P03 sin introducir microservicios, integraciones clínicas o infraestructura que el MVP no necesita. P04 fija componentes, límites, versiones, entornos, flujo de cambios y criterios técnicos; P05 conservará la responsabilidad sobre el modelo de datos.

## 2. Decisiones principales

| Área | Decisión |
|---|---|
| Estilo | Monolito modular con límites explícitos entre aplicaciones Django |
| Interfaz | HTML renderizado en servidor con mejora progresiva; sin SPA |
| Lenguaje | Python 3.13.x, última revisión de parche compatible |
| Framework | Django 5.2 LTS, última revisión 5.2.x |
| Base de datos | PostgreSQL 17.x; no usar SQLite en desarrollo ni pruebas |
| Contenedores | Docker Compose Specification, sin campo `version` obsoleto |
| Procesamiento | Servicios de aplicación; trabajos largos mediante worker único respaldado por PostgreSQL |
| Archivos | Volumen privado y adaptador de almacenamiento; nunca URL pública directa |
| Integración BI | Exportaciones versionadas; sin conexión automática con Power BI Service |
| Seguridad | Sesiones Django, usuario personalizado, permisos granulares y mínimo privilegio |
| Dependencias | `pyproject.toml` y archivo de bloqueo reproducible |
| Calidad | Pull request obligatorio, pruebas PostgreSQL, lint, tipos, seguridad y construcción de imagen |

## 3. Fundamento de versiones

- [Django 5.2](https://docs.djangoproject.com/en/5.2/releases/5.2/) es LTS, soporta Python 3.13 y recibe actualizaciones de seguridad durante al menos tres años.
- [Python 3.13](https://devguide.python.org/versions/) permanece en fase de correcciones y tiene fin de vida previsto para octubre de 2029.
- [PostgreSQL 17](https://www.postgresql.org/support/versioning/) recibe actualizaciones hasta noviembre de 2029; siempre se utilizará su revisión menor vigente.
- La [Compose Specification](https://docs.docker.com/reference/compose-file/) es el formato recomendado por Docker para describir servicios, redes y volúmenes.

La documentación registra series compatibles, no congela parches vulnerables. El archivo de bloqueo y las imágenes identificarán las revisiones exactas usadas en cada versión del software.

## 4. Expediente

- [Arquitectura y módulos](ARQUITECTURA.md)
- [Entornos, configuración y operación](ENTORNOS.md)
- [Seguridad y límites de confianza](SEGURIDAD.md)
- [Calidad, pruebas y CI](CALIDAD_CI.md)
- [Registro de decisiones](ARQUITECTURA.md#8-registro-de-decisiones-arquitectónicas)
- [Trazabilidad y puerta G04](TRAZABILIDAD_G04.md)

## 5. Resultado actual

P04 contiene 14 decisiones de arquitectura aceptadas, 12 módulos funcionales, 4 entornos, 17 controles de seguridad, 10 verificaciones de CI y 15 pruebas de aceptación arquitectónica. El 20 de agosto de 2026 el titular aprobó internamente los 12 controles de G04 y habilitó el avance hacia P05.
