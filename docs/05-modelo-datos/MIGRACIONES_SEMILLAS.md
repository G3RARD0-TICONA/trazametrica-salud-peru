# Migraciones, semillas y recuperación

## 1. Estrategia de migraciones

- Cada cambio de modelo genera una migración Django revisada junto con su código y prueba.
- Una migración integrada no se edita ni renumera; la corrección se realiza mediante otra migración.
- Se prohíbe `--fake` en los procedimientos ordinarios de local, CI y demo.
- Los cambios de datos usan `RunPython` con modelos históricos y funciones directa/inversa cuando la reversión sea segura.
- Una operación irreversible debe declararlo, justificarlo y exigir copia comprobada antes de demo.
- CI ejecutará `makemigrations --check --dry-run`, migración desde cero y actualización desde la última versión publicada.
- PostgreSQL 17 se utiliza en local, test, CI y demo; no existe ruta de migración validada con SQLite.

## 2. Orden inicial

| Orden | Aplicación | Dependencia de migración |
|---:|---|---|
| 1 | `accounts` | Usuario personalizado antes de cualquier FK de autoría |
| 2 | `organizations` | `accounts` |
| 3 | `processes` | `organizations`, `accounts` |
| 4 | `documents` | `processes`, `organizations`, `accounts` |
| 5 | `imports` | `documents`, `organizations`, `accounts` |
| 6 | `indicators` | `imports`, `processes`, `organizations`, `accounts` |
| 7 | `audits` | `documents`, `processes`, `organizations`, `accounts` |
| 8 | `improvements` | `audits`, `documents`, `accounts` |
| 9 | `risks` | `improvements`, `processes`, `organizations`, `accounts` |
| 10 | `reports` | `documents`, `accounts`; sin FK a cada tabla leída |
| 11 | `auditlog` | `accounts`; referencias funcionales desacopladas |

Las dependencias de migración no autorizan imports de presentación o acceso interno entre módulos.

## 3. Dataset sintético de referencia

El comando previsto `python manage.py seed_demo --version 1 --reset` deberá producir siempre el mismo conjunto lógico:

| Objeto | Cantidad mínima |
|---|---:|
| Organización | 1 |
| Sedes | 3 |
| Servicios | 20 |
| Áreas | 12 |
| Usuarios sintéticos | 16 |
| Roles | 8 |
| Procesos | 100 |
| Documentos/versiones | 150/220 |
| Indicadores/versiones | 200/260 |
| Observaciones KPI | 100 000 |
| Plantillas | 4 |
| Archivo mayor de prueba | 10 000 filas |
| Planes de auditoría | 12 |
| Hallazgos | 180 |
| Acciones correctivas | 240 |
| Riesgos | 150 |
| Controles | 120 |

Todos los nombres llevarán marcas ficticias y los archivos incluirán `DATOS SINTÉTICOS`. Está prohibido derivar semillas desde una base real, aunque se oculten nombres.

## 4. Determinismo e idempotencia

- La versión del dataset, una semilla pseudoaleatoria fija y un namespace UUID quedan registrados en el manifiesto.
- Los UUID de semilla se derivan de claves sintéticas estables; los registros creados por usuarios usan UUID aleatorios.
- Ejecutar la semilla sin `--reset` actualiza únicamente catálogos administrados y no duplica datos.
- `--reset` solo funcionará si `ENVIRONMENT` es local, test o demo y exige el marcador de base sintética.
- Fechas de negocio se generan respecto de una fecha de corte fija, no respecto de `now()`.
- Hashes, conteos y relaciones esperadas forman parte de la prueba de aceptación.

## 5. Protección contra datos reales

1. El generador no acepta archivos externos como fuente.
2. Dominios de correo usan `.invalid`; teléfonos, DNI, historias clínicas y diagnósticos no forman parte del esquema.
3. El validador bloquea patrones evidentes antes de persistir staging o archivos.
4. Un hallazgo de dato real detiene la carga, registra un evento técnico mínimo y activa el procedimiento de seguridad.
5. Logs, errores y bitácora no copian filas completas ni contenido de archivos.

## 6. Copia y restauración de demo

El respaldo demostrativo incluye:

- volcado PostgreSQL en formato definido por P18;
- manifiesto con versión de aplicación, migración final y dataset;
- inventario de `FileAsset` con tamaño y SHA-256;
- archivos sintéticos privados;
- fecha, herramienta y resultado de verificación.

Una restauración solo es conforme si migraciones, conteos, FK, restricciones, hashes y una muestra funcional pasan sus pruebas. P17 ejecutará el simulacro; P05 define el contrato.

## 7. Evolución del esquema

Un cambio incompatible requiere: impacto en requisitos y ADR, migración de esquema/datos, contrato de reversión, actualización del diccionario, prueba desde cero, prueba de actualización y, si afecta exportaciones, nueva versión de `ExportContract`. No se reutiliza una columna con un significado diferente.
