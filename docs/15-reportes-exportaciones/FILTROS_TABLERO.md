# Filtros del tablero

RF-028 se implementa sobre resultados KPI con los siguientes filtros combinables:

| Filtro | Regla |
|---|---|
| Periodo desde/hasta | Intersección con el periodo del resultado |
| Sede | FK exacta a sede activa |
| Servicio | FK exacta; si existe sede, debe pertenecer a ella |
| Proceso | Proceso del indicador |
| Indicador | Indicador exacto |
| Estado | Valor físico normalizado del resultado |

El fin no puede preceder al inicio, los UUID deben ser válidos y el estado solo acepta letras minúsculas y guion bajo. Los filtros válidos se serializan de forma canónica en el historial y dentro del archivo exportado.

El tablero muestra el total y la distribución por desempeño, además de hasta 50 resultados para consulta interactiva. Las exportaciones procesan como máximo 10 000 filas por ejecución.
