# Calidad, pruebas y CI

## 1. Flujo de cambios

1. Crear rama desde `main` actualizado.
2. Implementar un alcance identificado por requisitos.
3. Ejecutar comprobaciones locales.
4. Publicar un commit coherente y abrir pull request.
5. Integrar solo con verificaciones conformes y trazabilidad actualizada.

No se trabajará directamente sobre `main`. Los commits no mezclarán documentación, refactorizaciones y funciones no relacionadas.

## 2. Herramientas previstas

| Área | Herramienta/criterio |
|---|---|
| Formato y lint | Ruff |
| Tipos | mypy con soporte para Django |
| Pruebas | pytest y pytest-django |
| Cobertura | coverage.py; umbral crítico definido en P03 |
| Base de pruebas | PostgreSQL 17 de servicio |
| Dependencias | pip-audit y archivo bloqueado |
| Código inseguro | Bandit y revisión manual |
| Secretos | Escaneo automático y revisión de cambios |
| Contenedores | Construcción limpia y análisis de imagen |
| Documentación | Enlaces, identificadores, estados y Markdown |

Las versiones exactas se fijarán al crear `pyproject.toml` y el archivo de bloqueo. Agregar una herramienta requiere justificar qué falla detecta y quién atiende sus resultados.

## 3. Flujo de GitHub Actions

| Verificación | Evento | Condición de aprobación |
|---|---|---|
| `docs` | Pull request | Sin enlaces internos rotos ni estados contradictorios |
| `lint` | Pull request | Ruff sin errores |
| `types` | Pull request | mypy sin errores nuevos |
| `tests` | Pull request | Unitarias e integración PostgreSQL conformes |
| `coverage` | Pull request | Umbral de reglas críticas alcanzado |
| `migrations` | Pull request | Sin cambios de modelo pendientes y migraciones aplicables |
| `security` | Pull request | Sin secretos ni vulnerabilidades altas/críticas no aceptadas |
| `build` | Pull request | Imagen reproducible construida |
| `deploy-check` | Rama de demo | `check --deploy` conforme con configuración de demo |
| `acceptance` | Hito de parte | Casos de aceptación de la parte conformes |

En la fase documental algunos trabajos aún no existirán. La primera implementación de P04 deberá crear el flujo mínimo `docs`; la base de aplicación añadirá el resto.

## 4. Pirámide de pruebas

- **Unitarias:** políticas, cálculos, estados y validadores sin base cuando sea posible.
- **Integración:** ORM, restricciones, transacciones, permisos, archivos y PostgreSQL.
- **Aceptación:** flujos P03 mediante cliente HTTP y roles reales.
- **Sistema:** contenedores, worker, backup, exportaciones, rendimiento y seguridad.
- **Manual:** accesibilidad, claridad de errores y revisión visual.

## 5. Datos y determinismo

- Fábricas y semillas serán sintéticas, deterministas cuando la prueba lo necesite y aisladas.
- Ninguna prueba dependerá del orden global, red externa o fecha actual sin reloj controlado.
- Los hashes, fórmulas, zonas horarias y decimales tendrán casos límite explícitos.
- Las pruebas paralelas no compartirán archivos ni identificadores mutables.

## 6. Gestión de vulnerabilidades

Un hallazgo alto o crítico bloquea integración salvo excepción escrita con alcance, responsable, vencimiento y mitigación. Las excepciones no se ocultan ni se convierten en exclusiones permanentes. Dependencias fuera de soporte bloquean una versión pública.

## 7. Versionado y artefactos

- SemVer comenzará cuando exista software ejecutable.
- Cada versión conservará commit, lock de dependencias, migraciones, versión del dataset y notas.
- Imágenes y exportaciones se asociarán al commit que las produjo.
- Un release no se reconstruirá desde una rama mutable sin registrar el nuevo artefacto.
