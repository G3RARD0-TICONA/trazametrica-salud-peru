# Contratos de exportación

## Modelo

`ExportContract` identifica un conjunto, formato y consumidor mediante `code + version_no`. El esquema JSON conserva nombre, tipo, obligatoriedad y orden de cada columna; su representación canónica produce `schema_hash` SHA-256.

Los estados permitidos son `draft`, `published`, `superseded` y `annulled`. Publicar una nueva versión sustituye la versión publicada anterior dentro de una transacción. El contenido de una versión publicada o sustituida es inmutable.

`ExportRun` conserva el contrato exacto, actor solicitante, filtros normalizados, `FileAsset`, cantidad de filas, instante UTC y hash del resultado. Las ejecuciones no se eliminan físicamente.

## Metadatos RN-021

Cada fila tabular incluye, antes de las columnas funcionales:

1. `synthetic_marker`;
2. `contract_code`;
3. `contract_version`;
4. `schema_hash`;
5. `generated_at_utc`;
6. `filters_json`.

El PDF presenta los mismos datos en su cabecera. El XLSX conserva además código, versión y hash en la hoja oculta `META`.

## Compatibilidad RNF-014

La generación compara el esquema publicado con el esquema implementado. Una discrepancia bloquea la exportación en lugar de producir una ruptura silenciosa. Un cambio compatible o incompatible requiere una versión nueva y publicación explícita.
