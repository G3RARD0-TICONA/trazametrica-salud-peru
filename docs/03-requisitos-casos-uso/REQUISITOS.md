# Requisitos del MVP

Cada requisito es obligatorio salvo que una parte posterior documente y apruebe su cambio.

## 1. Requisitos funcionales

### Identidad y organización

| ID | Requisito verificable | Prioridad |
|---|---|---|
| RF-001 | Autenticar usuarios activos y rechazar credenciales inválidas sin revelar qué dato falló | MVP |
| RF-002 | Autorizar cada acción mediante roles y permisos evaluados en el servidor | MVP |
| RF-003 | Crear, editar, desactivar y consultar usuarios conservando su historial | MVP |
| RF-004 | Mantener organización, sedes, servicios, áreas y responsables con códigos únicos | MVP |
| RF-005 | Impedir la eliminación física de maestros utilizados y permitir su desactivación controlada | MVP |

### Procesos y documentos

| ID | Requisito verificable | Prioridad |
|---|---|---|
| RF-006 | Registrar procesos con código, objetivo, alcance, propietario, entradas, salidas y estado | MVP |
| RF-007 | Crear versiones de procesos y conservar la versión aprobada previamente | MVP |
| RF-008 | Registrar documentos administrativos con tipo, versión, vigencia, responsable y estado | MVP |
| RF-009 | Someter procesos y documentos a revisión, aprobación, rechazo y anulación motivada | MVP |

### Importación y calidad de datos

| ID | Requisito verificable | Prioridad |
|---|---|---|
| RF-010 | Publicar plantillas Excel identificadas por código y versión | MVP |
| RF-011 | Registrar archivo, versión de plantilla, hash, actor, fecha y estado de cada carga | MVP |
| RF-012 | Validar estructura, columnas, tipos, obligatoriedad, códigos, fechas, rangos y duplicados | MVP |
| RF-013 | Rechazar atómicamente una carga inválida y entregar errores por fila, columna y regla | MVP |
| RF-014 | Evitar la aceptación duplicada del mismo archivo y permitir reintentos trazables | MVP |

### Indicadores

| ID | Requisito verificable | Prioridad |
|---|---|---|
| RF-015 | Mantener fichas KPI con fórmula versionada, unidad, frecuencia, meta, sentido y responsable | MVP |
| RF-016 | Calcular resultados usando datos aceptados y la versión de fórmula vigente para el periodo | MVP |
| RF-017 | Conservar entradas, fórmula, resultado, fecha y ejecutor para reproducir cada cálculo | MVP |
| RF-018 | Revisar, aprobar, rechazar y publicar resultados sin sobrescribir valores aprobados | MVP |

### Auditoría, hallazgos y mejora

| ID | Requisito verificable | Prioridad |
|---|---|---|
| RF-019 | Planificar auditorías con alcance, criterios, responsable, fechas y estado | MVP |
| RF-020 | Ejecutar listas de verificación versionadas y registrar resultados por criterio | MVP |
| RF-021 | Registrar hallazgos y no conformidades con clasificación, evidencia, origen y responsable | MVP |
| RF-022 | Crear acciones correctivas con causa, tarea, responsable, fecha y criterio de eficacia | MVP |
| RF-023 | Alertar dentro de la aplicación sobre vencimientos próximos, vencidos y tareas sin responsable | MVP |
| RF-024 | Verificar eficacia y aprobar el cierre sin permitir autoaprobación | MVP |

### Evidencia, trazabilidad y salida

| ID | Requisito verificable | Prioridad |
|---|---|---|
| RF-025 | Adjuntar evidencia sintética con metadatos, hash y vínculo al objeto correspondiente | MVP |
| RF-026 | Registrar en bitácora actor, instante, objeto, acción, motivo y resultado de cambios críticos | MVP |
| RF-027 | Consultar bitácora con filtros sin permitir edición por usuarios ordinarios | MVP |
| RF-028 | Mostrar tableros con filtros por periodo, sede, servicio, proceso, indicador y estado | MVP |
| RF-029 | Exportar Excel, CSV y PDF marcados como `DATOS SINTÉTICOS` y registrar la exportación | MVP |
| RF-030 | Generar conjuntos tabulares estables y documentados para Power BI Desktop | MVP |
| RF-031 | Mantener un catálogo versionado de referencias normativas sin declarar cumplimiento | MVP |
| RF-032 | Regenerar o restablecer el conjunto de demostración sin depender de datos reales | MVP |

### Riesgos y controles

| ID | Requisito verificable | Prioridad |
|---|---|---|
| RF-033 | Registrar riesgos con proceso, causa, evento, consecuencia, probabilidad, impacto, nivel y responsable | MVP |
| RF-034 | Versionar evaluaciones, controles, fechas de revisión y riesgo residual sin sobrescribir aprobaciones | MVP |
| RF-035 | Vincular riesgos con procesos, indicadores, hallazgos y acciones, y alertar revisiones o controles vencidos | MVP |

### Estadística y analítica avanzada

| ID | Requisito verificable | Prioridad |
|---|---|---|
| RF-036 | Calcular descriptivos, distribuciones, atípicos, Pareto, gráficos de control, tendencias y medias móviles sobre datos sintéticos | MVP |
| RF-037 | Ejecutar regresión lineal y logística con separación cronológica entrenamiento/prueba, métricas y comparación contra línea base | MVP |
| RF-038 | Versionar definiciones analíticas y conservar entradas, parámetros, supuestos, limitaciones, métricas y hashes de cada ejecución | MVP |

## 2. Requisitos no funcionales

| ID | Requisito verificable | Evidencia esperada |
|---|---|---|
| RNF-001 | Aplicar mínimo privilegio, sesiones seguras, validación de entrada y controles inspirados en [OWASP ASVS 5.0](https://owasp.org/www-project-application-security-verification-standard/) nivel 1 | Pruebas de seguridad P17 |
| RNF-002 | Bloquear datos personales o clínicos evidentes en archivos y demostraciones | Validador y pruebas negativas |
| RNF-003 | No almacenar secretos en el repositorio, base de demostración, logs o exportaciones | Escaneo de secretos y revisión |
| RNF-004 | Conservar integridad transaccional: una operación crítica se completa totalmente o no produce cambios funcionales | Pruebas de rollback |
| RNF-005 | Reproducir el mismo cálculo con las mismas entradas y versión de fórmula | Prueba determinista |
| RNF-006 | Responder el 95 % de consultas ordinarias en ≤2 s con el conjunto base de demostración | Prueba de rendimiento |
| RNF-007 | Validar una importación de 10 000 filas en ≤60 s en el entorno de referencia | Prueba de carga documentada |
| RNF-008 | Alcanzar WCAG 2.2 nivel AA en los flujos primarios, sujeto a verificación manual y automática en P17 | Informe de accesibilidad |
| RNF-009 | Ejecutarse mediante instrucciones reproducibles en Windows y Linux usando configuración externa | Prueba de instalación limpia |
| RNF-010 | Mantener cobertura automatizada ≥80 % en reglas críticas y 100 % de sus caminos de rechazo definidos | Reporte de cobertura |
| RNF-011 | Producir logs estructurados sin datos sensibles y correlacionar errores con operaciones | Pruebas de observabilidad |
| RNF-012 | Presentar fechas y horas en `America/Lima`, conservar instante técnico inequívoco y usar español en la interfaz | Pruebas de localización |
| RNF-013 | Documentar copia, restauración y reinicio del entorno demostrativo | Simulacro de recuperación |
| RNF-014 | Versionar contratos de exportación para evitar cambios silenciosos que rompan Power BI | Pruebas de esquema |

## 3. Conjunto base de rendimiento

Las metas RNF-006 y RNF-007 se medirán con un conjunto sintético versionado que incluya, como mínimo, 3 sedes, 20 servicios, 100 procesos, 200 indicadores, 100 000 observaciones y un archivo de carga de 10 000 filas. P04 fijará el entorno de referencia y P05 el esquema generador.

Las referencias OWASP y WCAG orientan controles técnicos; el proyecto no afirmará certificación ni conformidad hasta completar las pruebas previstas.
