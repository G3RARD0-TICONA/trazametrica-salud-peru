# Trazabilidad, pruebas y puerta G03

## 1. Matriz de trazabilidad

| Origen | Necesidad | Requisitos | Casos de uso | Evidencia futura |
|---|---|---|---|---|
| P00 | Gobierno, roles y cambios controlados | RF-001–009, RF-026–027 | CU-01–05, CU-17 | Pruebas de acceso, versiones y bitácora |
| P01 | Excel y calidad de datos | RF-010–014 | CU-06–07 | Plantillas, cargas válidas y rechazos |
| P01 | KPI y Power BI Desktop | RF-015–018, RF-028–030 | CU-08–09, CU-16 | Cálculos reproducibles y exportaciones |
| P01 | Procesos, auditoría y mejora | RF-006–009, RF-019–024 | CU-04–05, CU-10–15 | Flujo proceso–hallazgo–acción–cierre |
| P00/P01 | Riesgos y controles de gestión | RF-033–035 | CU-20 | Evaluación, tratamiento, revisión y alertas |
| P01/P16 | Estadística y analítica administrativa | RF-036–038 | CU-21 | Métricas, línea base, hashes y rechazo de calidad |
| P02 | Datos sintéticos y límites clínicos | RF-025, RF-029, RF-031–032; RNF-002–003 | CU-07, CU-16, CU-18 | Validación negativa y marca sintética |
| P02 | Mínimo privilegio y trazabilidad | RF-002, RF-026–027; RNF-001, RNF-011 | CU-01–02, CU-17 | Denegaciones y eventos correlacionados |
| P02 | No certificación | RF-031; RN-024 | CU-16 | Revisión terminológica |

## 2. Pruebas de aceptación de alto nivel

| ID | Escenario | Resultado esperado |
|---|---|---|
| PA-03-01 | Usuario inactivo intenta autenticarse | Acceso denegado sin perder historial |
| PA-03-02 | Usuario sin permiso invoca una operación directa | Respuesta denegada y sin cambio funcional |
| PA-03-03 | Autor intenta aprobar su propia versión | Operación bloqueada y trazada |
| PA-03-04 | Se aprueba una nueva versión | Una sola versión vigente; anterior inmutable |
| PA-03-05 | Archivo válido de 10 000 filas | Aceptación completa dentro de la meta |
| PA-03-06 | Archivo contiene error bloqueante | Cero filas incorporadas y detalle accionable |
| PA-03-07 | Se reenvía un archivo aceptado | Duplicado detectado por hash |
| PA-03-08 | KPI se recalcula con mismas entradas y versión | Mismo resultado y trazabilidad completa |
| PA-03-09 | Se intenta sobrescribir KPI publicado | Operación bloqueada; se exige corrección versionada |
| PA-03-10 | Hallazgo sin criterio ni evidencia | Registro rechazado |
| PA-03-11 | Responsable intenta aprobar eficacia propia | Operación bloqueada |
| PA-03-12 | Acción no eficaz se verifica | Hallazgo permanece/reabre y exige nueva acción |
| PA-03-13 | Se exporta un tablero filtrado | Archivo con filtros, versión, fecha y marca sintética |
| PA-03-14 | Archivo contiene posible DNI o diagnóstico real | Carga bloqueada para revisión |
| PA-03-15 | Se consulta/modifica bitácora | Consulta autorizada; edición ordinaria denegada |
| PA-03-16 | Se restablece la demostración | Datos sintéticos conocidos y operación trazada |
| PA-03-17 | Se aprueba una nueva versión documental | Versión anterior inmutable y nueva vigencia única |
| PA-03-18 | Se intenta cerrar riesgo alto con control vencido | Cierre bloqueado y alerta trazada |

## 3. Riesgos y derivaciones

| Riesgo | Tratamiento en P03 | Parte que debe resolverlo |
|---|---|---|
| Alcance excesivo | MVP y funciones diferidas explícitas | P04 prioriza módulos |
| Fórmulas inseguras | Fórmula aprobada, versionada y reproducible | P04 diseña motor seguro |
| Evidencias maliciosas | Tipo, tamaño, nombre y hash obligatorios | P04/P17 implementan controles |
| Datos reales accidentales | Bloqueo preventivo y pruebas negativas | P05/P10/P17 |
| Roles demasiado amplios | Segregación y denegaciones explícitas | P06 |
| Ruptura de Power BI | Contrato de exportación versionado | P05/P15 |
| Rendimiento no reproducible | Conjunto y entorno de referencia | P04/P05/P17 |

## 4. Puerta G03

| N.º | Criterio | Estado |
|---:|---|---|
| 1 | Alcance funcional y exclusiones definidos | Conforme |
| 2 | Actores y responsabilidades identificados | Conforme |
| 3 | Matriz de permisos de alto nivel incluida | Conforme |
| 4 | Segregación de funciones definida | Conforme |
| 5 | Requisitos funcionales identificados y verificables | Conforme |
| 6 | Requisitos no funcionales medibles | Conforme |
| 7 | Reglas de negocio y estados mínimos definidos | Conforme |
| 8 | Casos de uso críticos con alternativas documentados | Conforme |
| 9 | Trazabilidad P00–P02 → requisito → caso → prueba | Conforme |
| 10 | Riesgos y decisiones diferidas asignados a partes posteriores | Conforme |
| 11 | Validación documental sin enlaces relativos rotos ni estados contradictorios | Conforme |
| 12 | Aprobación interna del titular registrada | Conforme |

**Resultado:** 12/12 controles conformes. El titular aprobó expresamente P03 y autorizó el cierre de G03 el 20 de agosto de 2026.

## 5. Efecto de aprobación

Cerrar G03 autorizará elaborar P04 y P05. No autorizará todavía programación productiva, datos reales ni ampliación clínica. Cualquier cambio posterior deberá actualizar requisito, caso de uso, prueba, impacto y versión.
