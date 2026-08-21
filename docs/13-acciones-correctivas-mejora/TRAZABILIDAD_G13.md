# Trazabilidad y puerta G13

## Requisitos

| Fuente | Evidencia P13 | Prueba |
|---|---|---|
| RF-022 / CU-12–13 | causa y acción correctiva aprobables | creación, rechazo, aprobación y ejecución |
| RF-023 / CU-15 | alerta derivada por fecha y responsable | vencido, próximo, en plazo e inactivo |
| RF-024 / CU-14 | revisión de eficacia y cierre | eficacia independiente, reapertura y RN-019 |
| RN-015–019 | servicios transaccionales y estados | bloqueos, reasignación y cierre condicionado |
| RNF-004 | operaciones atómicas | evidencia inválida sin persistencia parcial |
| ENT-035–038 | cuatro tablas, FK, constraints e índices | migración desde cero y `makemigrations --check` |

## Pruebas añadidas

- Causa por método permitido, envío y aprobación independiente.
- Autoaprobación causal bloqueada.
- Acción impedida antes de aprobar la causa RN-015.
- Responsable, fecha y criterio obligatorios RN-016.
- Plan aprobado por actor distinto de su autor.
- Evidencia rechazada sin vínculo parcial.
- Envío a verificación bloqueado sin evidencia.
- Responsable/ejecutor impedido de aprobar eficacia RN-018.
- Resultado eficaz que cierra acción y hallazgo cuando corresponde.
- Resultado no eficaz que reabre acción y hallazgo.
- Cierre impedido mientras existe otra acción obligatoria abierta RN-019.
- Responsable inactivo visible y reasignación motivada RN-017.
- Catálogo HTTP 403/200 con marca sintética.
- Alertas vencido, próximo, en plazo, inactivo y no aplicable.
- Semilla idempotente 12/24/18/15.

## Evaluación actual de G13

Las verificaciones locales aprobaron 124 pruebas aplicables y 83 % de cobertura. Las CI #56 y #57 aprobaron 125 pruebas sobre PostgreSQL 17, mantuvieron 83 % de cobertura y verificaron documentación, lint, tipado, migraciones, seguridad, dependencias y construcción del contenedor. El titular autorizó expresamente el cierre de G13 el 21 de agosto de 2026.

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance trazado a P03/P05 | RF, CU, RN, RNF y ENT identificadas | Conforme |
| 2 | ENT-035–038 implementadas | modelos, migraciones, constraints e índices | Conforme |
| 3 | Causa raíz controlada | método, análisis, conclusión y aprobación segregada | Conforme |
| 4 | Plan correctivo RN-015/016 | causa aprobada, tarea, responsable, fecha y criterio | Conforme |
| 5 | Evidencia sintética RN-020 | archivo limpio, SHA-256, descripción y rollback | Conforme |
| 6 | Alertas y reasignación RF-023/RN-017 | fecha derivada, responsable inactivo e historial | Conforme |
| 7 | Eficacia independiente RN-018 | responsable y ejecutor no revisan su acción | Conforme |
| 8 | Cierre condicionado RN-019 | todas las acciones obligatorias eficaces | Conforme |
| 9 | Historia protegida | bitácora, `PROTECT`, sin update/delete masivo | Conforme |
| 10 | Semilla contractual | 12 causas, 24 acciones, 18 evidencias y 15 revisiones | Conforme |
| 11 | CI en Python 3.13/PostgreSQL 17 | CI #56 y #57: 125 pruebas, 83 %, seguridad, dependencias e imagen conformes | Conforme |
| 12 | Aceptación formal del titular | Autorización expresa registrada el 21 de agosto de 2026 | Conforme |

**Resultado final:** 12/12. P13 está **APROBADA INTERNAMENTE** y G13 queda cerrada. Esta aprobación interna no representa certificación, autorización sanitaria ni aptitud productiva.
