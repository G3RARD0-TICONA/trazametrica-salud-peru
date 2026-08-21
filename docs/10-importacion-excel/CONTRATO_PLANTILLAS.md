# Contrato de plantillas

Cada versión define de 1 a 100 columnas en JSON normalizado. El orden forma parte del contrato y su representación canónica produce `schema_hash` SHA-256.

## Reglas disponibles

| Clave | Uso |
|---|---|
| `name` | identificador `snake_case` único |
| `type` | `string`, `integer`, `decimal`, `date` o `boolean` |
| `required` | obligatoriedad |
| `max_length` | longitud máxima de texto, hasta 500 |
| `pattern` | expresión regular de código |
| `choices` | catálogo cerrado |
| `min` / `max` | rango numérico inclusivo |
| `allow_future` | excepción explícita para fechas planificadas |
| `unique_in_file` | valor único dentro del archivo |

## Estructura XLSX

- `DATOS`: marca en la fila 1, encabezados en la fila 2 y datos desde la fila 3.
- `INSTRUCCIONES`: tipo, obligatoriedad y reglas de cada columna.
- `META`: código, número de versión y hash; se genera oculta y no debe alterarse.

Solo una versión vigente puede descargarse. Una nueva publicación sustituye la anterior sin borrar su historial. El formato OOXML se genera mediante un adaptador interno sustituible; P15 podrá cambiar la biblioteca de presentación sin modificar el dominio ni el esquema.
