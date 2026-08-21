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

Las verificaciones locales aprobaron 67 pruebas aplicables y 86 % de cobertura. CI y aceptación formal siguen pendientes.

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
| 11 | CI en Python 3.13/PostgreSQL 17 | Pendiente de ejecución en GitHub | Pendiente |
| 12 | Aceptación formal del titular | Requiere autorización expresa posterior | Pendiente |

**Resultado actual:** 10/12. P09 está **EN PRUEBAS** y G09 permanece abierta. La aceptación interna no representa certificación, autorización sanitaria ni aptitud productiva.
