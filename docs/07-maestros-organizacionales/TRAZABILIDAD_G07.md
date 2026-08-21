# Trazabilidad y puerta G07

## 1. Requisitos cubiertos

| Fuente | Evidencia P07 | Prueba |
|---|---|---|
| RF-004 | Cinco entidades, códigos y responsables | creación, edición, jerarquía y vigencias |
| RF-005 | `PROTECT`, desactivación y bloqueo de `delete` | instancia, queryset y dependencias |
| CU-03 | Selector y vista protegida de estructura | 403 sin capacidad y 200 con `VIEWER` |
| RN-001 | Código normalizado y único por ámbito | duplicado por mayúsculas/minúsculas |
| RN-002 | Historial sin eliminación física | pruebas de borrado y desactivación |
| RNF-004 | Servicios atómicos | denegación sin mutación e integridad DB |
| ADR-005 | Una organización activa | servicio e índice único parcial |
| ENT-004–008 | Migración `organizations.0001_initial` | `makemigrations --check` y migración limpia |

## 2. Pruebas automatizadas

- Singleton de organización activa.
- Normalización y unicidad de códigos.
- Edición con actor de auditoría.
- Bloqueo de borrado por instancia y queryset.
- Orden obligatorio de desactivación.
- Prevención de ciclos de áreas.
- Superposición y cierre de responsabilidades.
- Restricción PostgreSQL de fechas.
- Denegación por falta de capacidad sin efecto parcial.
- Vista de lectura según rol.
- Semilla determinista e idempotente con conteos de P05.
- Correspondencia exacta de las cinco tablas físicas.

La ejecución CI #19 del PR #6 aprobó las 36 pruebas en PostgreSQL 17.11, obtuvo 86 % de cobertura total, no registró hallazgos en Bandit ni vulnerabilidades conocidas en `pip-audit`, y construyó correctamente la imagen del contenedor.

## 3. Evaluación de G07

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado a P03/P05 | RF-004/005, CU-03 y ENT-004–008 | Conforme |
| 2 | Cinco entidades y relaciones implementadas | Modelos y migración inicial | Conforme |
| 3 | Códigos únicos por ámbito | Constraints con `Lower` | Conforme |
| 4 | Una organización activa | Servicio e índice único parcial | Conforme |
| 5 | Desactivación sin borrado | Modelo, queryset y servicio | Conforme |
| 6 | Jerarquía de áreas segura | Constraint y detección de ciclos | Conforme |
| 7 | Responsabilidades con vigencia | Servicio, índice y constraint | Conforme |
| 8 | Autorización en servidor | Capacidades P06 y pruebas negativas | Conforme |
| 9 | Consulta organizacional protegida | Selector, vista y plantilla | Conforme |
| 10 | Dataset sintético reproducible | 1/3/20/12 y UUIDv5 | Conforme |
| 11 | CI completa en PostgreSQL 17 | Ejecución #19: pruebas, 86 % de cobertura, seguridad, dependencias e imagen | Conforme |
| 12 | Aceptación formal del titular | Decisión posterior a CI | Pendiente |

**Resultado actual:** 11/12. P07 está **EN PRUEBAS** y G07 permanece abierta únicamente por la aceptación formal del titular. Su eventual cierre no significará certificación, autorización sanitaria o aptitud productiva.
