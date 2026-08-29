# PDF y seguridad de exportaciones

El adaptador PDF produce un documento PDF 1.4 paginado con fuente estándar, tabla textual y metadatos visibles: marca sintética, contrato, versión, hash de esquema, instante UTC, filtros y cantidad de filas.

Controles aplicados a todos los formatos:

- autorización en servidor para cada solicitud;
- contrato publicado obligatorio;
- máximo de 10 000 filas;
- nombre generado por el sistema y clave opaca bajo `reports/`;
- SHA-256 calculado sobre el contenido final;
- `FileAsset` marcado sintético y limpio solo por el generador controlado;
- cabeceras `Content-Disposition`, `X-Content-Type-Options`, ejecución y hash;
- evento auditable `report.exported`.

P17/P18 deberán añadir almacenamiento privado definitivo, descarga temporal y verificación integral de rendimiento. El estado demostrativo no acredita seguridad productiva.
