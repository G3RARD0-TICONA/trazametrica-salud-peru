# Trazabilidad y puerta G08

## 1. Requisitos cubiertos

| Fuente | Evidencia P08 | Prueba |
|---|---|---|
| RF-008 | Catálogo, tipo, versión, vigencia, responsable y estado | creación, unicidad y consulta |
| RF-009 | Revisión, aprobación, rechazo, anulación y bitácora | transiciones y eventos |
| CU-05 | Aprobación independiente y una vigencia | autor distinto y sustitución |
| CU-19 | Registro de documentos y referencias | servicios, selectores y vista |
| RN-003/004 | Una vigencia y versión inmutable | superposición y cambio bloqueado |
| RN-005/006 | Sin autoaprobación; motivo obligatorio | pruebas negativas |
| RN-020 | Hash, tipo, tamaño, fecha y estado de archivo | validación de `FileAsset` |
| RN-024 | Sin afirmar certificación | filtro de frases y advertencias |
| ENT-012–016/046 | Modelos, constraints e índices | migraciones y nombres físicos |

## 2. Pruebas automatizadas añadidas

- Normalización y unicidad de código documental.
- Coherencia entre organización y área responsable.
- Metadatos de archivo sintético, extensión, MIME, tamaño, ruta y hash.
- Carga lógica de texto o archivo limpio, nunca ambos.
- Numeración y hash deterministas.
- Prohibición de autoaprobación.
- Aprobación independiente, vigencia e inmutabilidad.
- Sustitución con inicio futuro sin terminar anticipadamente el estado vigente.
- Motivo de anulación y desactivación ordenada.
- Denegación por falta de capacidad.
- Bloqueo de afirmaciones de certificación.
- Versionado y aprobación independiente de referencias.
- Inmutabilidad del dominio documental y ENT-046.
- Catálogo HTTP 403/200 según `documents.view`.
- Correspondencia de las seis tablas físicas.

## 3. Evaluación actual de G08

La ejecución #34 de GitHub Actions del PR #7 aprobó 56 pruebas en PostgreSQL 17.11 y Python 3.13.15, con 86 % de cobertura. También aprobó migraciones, tipado, lint, Bandit, `pip-audit` y construcción del contenedor.

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado a P03/P05 | RF, CU, RN y ENT identificadas | Conforme |
| 2 | Cinco entidades documentales implementadas | Modelos y migración inicial | Conforme |
| 3 | Flujo y estados controlados | Servicios transaccionales | Conforme |
| 4 | Separación autor/aprobador | Política y prueba negativa | Conforme |
| 5 | Vigencias sin superposición | Bloqueo y sustitución ordenada | Conforme |
| 6 | Contenido aprobado inmutable | Modelo, hash y pruebas | Conforme |
| 7 | Archivos sintéticos seguros | Lista permitida y metadatos íntegros | Conforme |
| 8 | Referencias sin sobreafirmaciones | Validación y advertencia visible | Conforme |
| 9 | Auditoría append-only | ENT-046 y eventos de servicio | Conforme |
| 10 | Consulta autorizada | `documents.view`, selector y HTTP 403/200 | Conforme |
| 11 | CI en Python 3.13/PostgreSQL 17 | Ejecución #34: 56 pruebas, 86 % e imagen correcta | Conforme |
| 12 | Aceptación formal del titular | Autorización expresa del 20 de agosto de 2026 | Conforme |

**Resultado final:** 12/12. P08 está **APROBADA INTERNAMENTE** y G08 queda cerrada. Esta decisión aprueba el incremento dentro del gobierno del proyecto; no representa certificación, autorización sanitaria ni aptitud productiva.
