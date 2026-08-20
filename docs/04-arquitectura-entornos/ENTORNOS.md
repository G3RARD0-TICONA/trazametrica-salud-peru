# Entornos, configuración y operación

## 1. Matriz de entornos

| Entorno | Propósito | Base | Datos | Ejecución |
|---|---|---|---|---|
| Local | Desarrollo interactivo | PostgreSQL 17 en contenedor | Sintéticos regenerables | Docker Compose o Python nativo |
| Test | Pruebas automatizadas aisladas | PostgreSQL efímero | Fábricas sintéticas | `pytest` |
| CI | Validación de cada pull request | Servicio PostgreSQL 17 | Fábricas sintéticas | GitHub Actions |
| Demo | Presentación controlada | PostgreSQL 17 persistente | Dataset versionado | Contenedores Linux |

SQLite queda prohibido para evitar diferencias de tipos, restricciones, transacciones y consultas respecto de PostgreSQL.

## 2. Servicios de Compose

| Servicio | Función | Exposición |
|---|---|---|
| `web` | Aplicación Django y servidor de desarrollo/demo | Puerto local o proxy |
| `worker` | Procesamiento de importaciones y trabajos persistentes | Sin puerto público |
| `db` | PostgreSQL 17 con volumen nombrado | Solo red interna; puerto opcional local |
| `proxy` | HTTPS, cabeceras y archivos estáticos en demo | Solo demo |

`compose.yaml` seguirá la Compose Specification y no incluirá el campo superior `version`, declarado obsoleto por Docker. Las imágenes base se fijarán por etiqueta de parche y digest cuando se cree una versión.

## 3. Política de versiones

| Componente | Restricción | Actualización |
|---|---|---|
| Python | `>=3.13,<3.14` | Último parche 3.13.x probado |
| Django | `>=5.2,<5.3` | Último parche 5.2.x disponible |
| PostgreSQL | Serie 17 | Última revisión menor |
| Psycopg | Serie 3 compatible | Dependencia bloqueada |
| Dependencias Python | Versiones exactas en lock | Renovación controlada y pruebas |
| Compose | Especificación vigente | CLI soportada por Docker |

Las versiones se revisarán mensualmente y ante avisos de seguridad. Una actualización mayor requiere ADR y pruebas de migración.

## 4. Configuración

Los ajustes se separarán en `base`, `local`, `test` y `demo`. Toda configuración variable se suministrará mediante entorno o archivo secreto no versionado.

Variables mínimas:

| Variable | Secreta | Uso |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | No | Selección de entorno |
| `DJANGO_SECRET_KEY` | Sí | Firma criptográfica |
| `DJANGO_ALLOWED_HOSTS` | No | Hosts explícitos |
| `DATABASE_HOST/PORT/NAME/USER/PASSWORD` | Parcial | Conexión PostgreSQL |
| `DJANGO_SECURE_SSL_REDIRECT` | No | HTTPS en demo |
| `APP_TIME_ZONE` | No | Debe ser `America/Lima` |
| `MAX_UPLOAD_BYTES` | No | Límite de archivos |
| `DEMO_DATASET_VERSION` | No | Dataset sintético activo |

`.env.example` contendrá nombres y valores no sensibles. Ningún secreto real se almacenará en `.env.example`, Dockerfile, Compose, pruebas, documentación o acciones.

## 5. Inicio reproducible

El objetivo de P04 es que P05 y la construcción entreguen estos comandos estables:

```bash
docker compose up --build
docker compose exec web python src/manage.py migrate
docker compose exec web python src/manage.py seed_demo --reset
docker compose exec web python src/manage.py check
```

La aplicación deberá exponer comprobaciones separadas de vida y preparación. `web` no se considerará preparado hasta validar configuración y conexión a PostgreSQL.

## 6. Base de datos y transacciones

- Django usará `READ COMMITTED` por defecto y `transaction.atomic()` en mutaciones críticas.
- Pruebas de integración se ejecutarán contra PostgreSQL, no sustitutos.
- Migraciones serán parte del código y se comprobará que no existan cambios de modelo sin migración.
- El pool de conexiones no se habilitará hasta medir necesidad; evita una dependencia prematura.
- Fechas técnicas se almacenarán con zona horaria y se mostrarán en `America/Lima`.

## 7. Archivos, copia y recuperación

- Evidencias y cargas residirán en volumen privado, con nombre generado y hash.
- La descarga pasará por autorización; el proxy no servirá evidencias directamente.
- El backup de demo incluirá volcado PostgreSQL, manifiesto de versiones y archivos sintéticos.
- La restauración se probará en P17; copiar archivos sin su manifiesto no constituye respaldo válido.
- El dataset de demostración podrá reconstruirse desde generadores versionados.

## 8. Despliegue

`runserver` se limitará a local. Demo usará un servidor WSGI compatible detrás de proxy HTTPS y ejecutará `manage.py check --deploy`, conforme a la [lista oficial de despliegue de Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/). P18 definirá proveedor, dominio, costos y procedimiento de publicación.
