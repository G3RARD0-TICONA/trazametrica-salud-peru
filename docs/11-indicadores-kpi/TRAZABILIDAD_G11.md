# Trazabilidad y puerta G11

## Requisitos

| Fuente | Evidencia P11 | Prueba |
|---|---|---|
| RF-015 / CU-08 | `Indicator`, `IndicatorVersion` y flujo de ficha | versión, rechazo, aprobación e inmutabilidad |
| RF-016 / RN-011 | fórmula efectiva para el periodo y observaciones P10 | vigencia, ámbito y roles bloqueantes |
| RF-017 / RNF-005 | `ResultInput`, hashes y motor decimal | reproducción determinista |
| RF-018 / RN-012 | flujo de resultado y `supersedes` | autoaprobación bloqueada y corrección histórica |
| RN-013 | estado derivado de meta, umbral y sentido | en meta, advertencia y fuera de meta |
| ENT-022–026 | cinco tablas, FK, constraints e índices | migración desde cero y `makemigrations --check` |

## Pruebas locales

- Fórmula canónica, hash y porcentaje reproducible.
- Operadores ejecutables, claves adicionales y profundidad excesiva rechazados.
- Entradas vacías, roles distintos, división entre cero y no finitos rechazados.
- Autor de ficha y calculador impedidos de aprobar/publicar su propio trabajo.
- Materialización referencial y rollback total ante catálogo inexistente.
- Resultado decimal, entradas, estado automático, publicación y corrección trazables.
- Modelos protegidos contra actualización masiva y eliminación.
- Catálogo HTTP 403/200 con marca sintética.
- Semilla idempotente verificada con 200 KPI, 260 versiones y muestra de 1 000 observaciones.
- Generación completa verificada localmente con 100 000 observaciones sintéticas en 10,2 segundos; el CI valida PostgreSQL con una muestra determinista de 1 000 observaciones, sin presentar el tiempo local como benchmark productivo.

## Evaluación actual de G11

El CI #48 aprobó 104 pruebas sobre PostgreSQL 17 y 83 % de cobertura. La aceptación formal es el único control pendiente.

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado a P03/P05 | RF, CU, RN, RNF y ENT identificadas | Conforme |
| 2 | ENT-022–026 implementadas | modelos, migración, constraints e índices | Conforme |
| 3 | Ficha versionada y segregada | autor, aprobador, vigencia e inmutabilidad | Conforme |
| 4 | Fórmula declarativa segura | lista positiva, límites, SHA-256 y sin evaluación dinámica | Conforme |
| 5 | Observaciones desde P10 | carga procesada, ámbito, atomicidad y fila fuente | Conforme |
| 6 | Cálculo reproducible | decimal, versión, entradas, posiciones y hash | Conforme |
| 7 | Estado automático RN-013 | meta, umbral y sentido evaluados | Conforme |
| 8 | Revisión y publicación independiente | flujo y permisos negativos | Conforme |
| 9 | Correcciones sin sobrescritura | resultado anterior y `supersedes` conservados | Conforme |
| 10 | Consulta y semilla sintética | HTTP protegido y catálogo 200/260/100 000 | Conforme |
| 11 | CI en Python 3.13/PostgreSQL 17 | CI #48: 104 pruebas, 83 % de cobertura, seguridad, dependencias y contenedor conformes | Conforme |
| 12 | Aceptación formal del titular | Requiere autorización expresa posterior | Pendiente |

**Resultado actual:** 11/12. P11 está **EN REVISIÓN** y G11 permanece abierta únicamente por la aceptación del titular. La aprobación interna no representa certificación, autorización sanitaria ni aptitud productiva.
