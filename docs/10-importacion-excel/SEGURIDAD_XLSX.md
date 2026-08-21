# Seguridad XLSX

## Controles P10

| Riesgo | Control |
|---|---|
| Archivo falso | firma ZIP y estructura mínima OOXML |
| ZIP bomb | máximo 200 partes, 50 MiB expandidos y relación de compresión acotada |
| Path traversal | rutas absolutas o con `..` rechazadas |
| Macros/objetos | `vbaProject`, embeddings y conexiones rechazados |
| Vínculos externos | relaciones externas y `externalLinks` rechazados |
| Fórmulas | cualquier celda con `<f>` es error bloqueante |
| XML hostil | análisis mediante `defusedxml` |
| Datos reales | marca obligatoria, columnas prohibidas y dominios distintos de `.invalid` bloqueados |
| Exposición | errores genéricos y bitácora sin contenido de fila |

P10 no ejecuta fórmulas ni confía en valores precalculados. Los binarios cargados no se publican ni se incorporan al repositorio. El almacenamiento privado productivo, análisis antimalware real, cuotas y limpieza de archivos se validarán en P17/P18.
