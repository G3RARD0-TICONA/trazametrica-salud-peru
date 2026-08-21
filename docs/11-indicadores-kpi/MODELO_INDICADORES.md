# Modelo de indicadores

## Entidades ENT-022–026

| Entidad | Responsabilidad | Invariantes principales |
|---|---|---|
| `Indicator` | Identidad estable del KPI | código único por organización; proceso del mismo ámbito; responsable activo |
| `IndicatorVersion` | Ficha y fórmula versionadas | número único; fórmula con hash; vigencia no invertida; contenido enviado inmutable |
| `IndicatorObservation` | Valor fuente sintético | carga P10 procesada; periodo válido; sede/servicio coherentes; fila fuente única |
| `IndicatorResult` | Cálculo y decisión | decimal `numeric(20,6)`; hash único; publicación independiente; corrección enlazada |
| `ResultInput` | Evidencia de entradas | observación sin repetir; rol y posición únicos por resultado |

## Ámbito y precisión

El resultado puede representar a toda la organización, una sede o un servicio. Si existe servicio, debe pertenecer a la sede informada. Valores y resultados usan `DecimalField(20,6)`; se prohíbe `float` en cálculo y persistencia.

## Vigencia

Una versión `effective` cubre cálculos actuales. Una versión `superseded` puede reproducir periodos históricos dentro de sus fechas. Versiones en borrador, revisión, anuladas o fuera del intervalo no calculan resultados.

## Inmutabilidad

El código y metadatos controlados no se eliminan físicamente. Una ficha enviada no cambia fórmula ni definición. Una observación no se actualiza. Un resultado publicado conserva valor, entradas, fórmula, periodo, ámbito y hash; una corrección crea otro resultado con `supersedes`.
