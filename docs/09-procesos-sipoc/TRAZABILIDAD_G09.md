# Trazabilidad y puerta G09

## 1. Requisitos cubiertos

| Fuente | Evidencia P09 | Prueba |
|---|---|---|
| RF-006 | código, objetivo, alcance, propietario, entradas, actividades, salidas y estado | creación, ficha y consulta |
| RF-007 | versiones consecutivas e historial preservado | numeración, hash y sustitución |
| RF-009 | revisión, aprobación, rechazo, anulación y bitácora | transiciones y eventos |
| CU-04/05 | registrar, versionar y aprobar sin autoaprobación | servicios y prueba negativa |
| RN-001/002 | código único, no reutilización y sin borrado físico | constraints y bloqueos |
| RN-003/004 | una vigencia y ficha inmutable | sustitución y cambio bloqueado |
| RN-005/006 | segregación y motivo obligatorio | pruebas negativas |
| ENT-009–011 | modelos, constraints, índices y migraciones | correspondencia física |
| ENT-013 | vínculo documental diferido materializado | misma organización y relación inversa |

## 2. Pruebas añadidas

- Normalización, unicidad y edición controlada de metadatos.
- Coherencia entre organización y área propietaria.
- Hash recalculado al editar ficha o SIPOC.
- SIPOC completo obligatorio para revisión.
- Creación, edición y retiro motivado de elementos en borrador.
- Autoaprobación prohibida y aprobación independiente.
- Inmutabilidad de ficha y SIPOC después del envío.
- Rechazo, anulación y desactivación con motivo.
- Sustitución de versión efectiva sin perder historia.
- Vínculo documento–proceso autorizado y dentro del mismo ámbito.
- Eliminación física bloqueada.
- Catálogo y ficha HTTP 403/200 según `processes.view`.
- Semilla idempotente de 100/100/500 y distribución 10/60/30.

## 3. Evaluación actual de G09

La ejecución #39 de GitHub Actions del PR #8 aprobó 68 pruebas en PostgreSQL 17.11 y Python 3.13.15, con 86 % de cobertura. También aprobó migraciones, tipado, lint, Bandit, `pip-audit` y construcción del contenedor. El titular autorizó expresamente el cierre y la integración el 20 de agosto de 2026.

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado a P03/P05 | RF, CU, RN y ENT identificadas | Conforme |
| 2 | ENT-009–011 implementadas | modelos, migración, constraints e índices | Conforme |
| 3 | Ficha mínima y SIPOC completo | validación de las cinco secciones | Conforme |
| 4 | Versionado e historial | numeración, hash y estados | Conforme |
| 5 | Separación autor/aprobador | política y prueba negativa | Conforme |
| 6 | Vigencias sin superposición | servicio transaccional y sustitución | Conforme |
| 7 | Contenido aprobado inmutable | modelo, servicios y pruebas | Conforme |
| 8 | Documento vinculado con integridad | FK protegida, ámbito y prueba | Conforme |
| 9 | Auditoría append-only | eventos de servicio | Conforme |
| 10 | Consulta y semilla sintética | HTTP 403/200 y 100/100/500 | Conforme |
| 11 | CI en Python 3.13/PostgreSQL 17 | Ejecución #39: 68 pruebas, 86 % e imagen correcta | Conforme |
| 12 | Aceptación formal del titular | Autorización expresa del 20 de agosto de 2026 | Conforme |

**Resultado final:** 12/12. P09 está **APROBADA INTERNAMENTE** y G09 queda cerrada. Esta decisión aprueba el incremento dentro del gobierno del proyecto; no representa certificación, autorización sanitaria ni aptitud productiva.
