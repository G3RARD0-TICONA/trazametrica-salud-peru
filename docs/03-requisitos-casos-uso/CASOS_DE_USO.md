# Casos de uso

## 1. Catálogo

| ID | Caso de uso | Actor principal | Resultado |
|---|---|---|---|
| CU-01 | Iniciar y cerrar sesión | A01–A08 | Sesión válida y trazable |
| CU-02 | Administrar usuarios y roles | A01 | Acceso configurado sin borrar historia |
| CU-03 | Mantener organización, sedes y servicios | A01 | Maestros disponibles y versionados cuando corresponda |
| CU-04 | Registrar y versionar un proceso | A02/A03 | Versión en revisión |
| CU-05 | Aprobar una versión | A07 | Versión vigente sin autoaprobación |
| CU-06 | Descargar plantilla Excel | A04/A05 | Plantilla vigente identificada |
| CU-07 | Importar y validar datos | A04/A05 | Carga aceptada o errores accionables |
| CU-08 | Definir o versionar un KPI | A04 | Ficha y fórmula en revisión |
| CU-09 | Calcular y publicar un KPI | A04/A07 | Resultado reproducible publicado |
| CU-10 | Planificar y ejecutar auditoría | A02/A06 | Evaluación concluida |
| CU-11 | Registrar hallazgo o no conformidad | A02/A06 | Hallazgo trazado y asignado |
| CU-12 | Analizar causa y crear plan correctivo | A02/A03 | Acciones aprobables |
| CU-13 | Ejecutar acción y adjuntar evidencia | A03 | Acción lista para verificación |
| CU-14 | Verificar eficacia y cerrar | A02/A07 | Cierre independiente o reapertura |
| CU-15 | Consultar alertas y pendientes | A02–A07 | Trabajo priorizado |
| CU-16 | Consultar tablero y exportar | A02–A08 | Salida filtrada y marcada |
| CU-17 | Consultar bitácora | A01/A02/A07 | Historia de operación visible |
| CU-18 | Restablecer datos de demostración | A01 | Entorno sintético conocido |
| CU-19 | Registrar y versionar documento administrativo | A02/A03/A07 | Documento vigente y anterior inmutable |
| CU-20 | Evaluar riesgo y revisar controles | A02/A03/A07 | Riesgo residual y tratamiento trazables |

## 2. Casos críticos detallados

### CU-05 — Aprobar una versión

- **Precondiciones:** versión en revisión; autor y aprobador identificados; campos obligatorios completos.
- **Flujo principal:** A07 abre la versión, compara cambios y evidencia, registra decisión; el sistema verifica competencia y separación; aprueba, cierra la vigencia anterior cuando corresponde y registra bitácora.
- **Alternativas:** si el aprobador es autor, falta evidencia o existe conflicto de vigencia, se deniega; A07 puede rechazar con motivo y devolver a borrador.
- **Postcondición:** existe como máximo una versión vigente y el historial anterior permanece inmutable.

### CU-07 — Importar y validar datos

- **Precondiciones:** usuario autorizado; plantilla vigente; archivo sintético dentro del límite permitido.
- **Flujo principal:** el actor carga el archivo; A09 calcula hash, identifica plantilla y ejecuta validaciones; si no hay errores bloqueantes, registra la aceptación y procesa todas las filas en una transacción.
- **Alternativas:** formato desconocido, duplicado, estructura incorrecta o regla fallida producen rechazo sin incorporación parcial; se entrega detalle por fila, columna, código y recomendación.
- **Postcondición:** la carga queda aceptada y trazable, o rechazada con errores reproducibles.

### CU-09 — Calcular y publicar un KPI

- **Precondiciones:** ficha y fórmula aprobadas; datos del periodo aceptados; responsable asignado.
- **Flujo principal:** A04 solicita cálculo; A09 fija entradas y versión, calcula y guarda resultado; A04 revisa; A07 aprueba y publica.
- **Alternativas:** ausencia de datos, fórmula no vigente, división inválida o resultado fuera de regla bloquean publicación y generan diagnóstico.
- **Postcondición:** el resultado publicado puede reproducirse y no se sobrescribe.

### CU-11 — Registrar hallazgo o no conformidad

- **Precondiciones:** auditoría en ejecución o fuente alternativa identificada.
- **Flujo principal:** A06/A02 selecciona criterio, describe condición y evidencia, clasifica impacto, asigna responsable y fecha; el sistema crea el hallazgo abierto y notifica dentro de la aplicación.
- **Alternativas:** falta de criterio, descripción o evidencia/justificación impide el registro.
- **Postcondición:** hallazgo trazado al origen, criterio, actor y evidencia.

### CU-14 — Verificar eficacia y cerrar

- **Precondiciones:** acciones obligatorias terminadas; evidencia adjunta; verificador distinto del responsable.
- **Flujo principal:** A02/A07 evalúa el criterio de eficacia; si se cumple, aprueba acción y cierre; A09 registra fechas, responsables y eventos.
- **Alternativas:** evidencia insuficiente, acción vencida, autoaprobación o resultado no eficaz mantienen/reabren el hallazgo y exigen nueva acción.
- **Postcondición:** cierre independiente sustentado o reapertura trazable.

### CU-16 — Consultar tablero y exportar

- **Precondiciones:** usuario autorizado; datos publicados; filtros válidos.
- **Flujo principal:** el actor filtra; el sistema presenta KPI y estados; el actor exporta; A09 incluye filtros, versión, fecha y marca sintética, y registra el evento.
- **Alternativas:** volumen excesivo exige acotar filtros; permiso insuficiente o dato no publicado impide la salida.
- **Postcondición:** archivo reproducible y trazado sin datos reales.

## 3. Regla de aceptación

Cada caso deberá probar flujo principal, permisos, al menos una alternativa bloqueante, bitácora y postcondición. Los detalles de interfaz se definirán después de validar el comportamiento y no sustituyen estas pruebas.
