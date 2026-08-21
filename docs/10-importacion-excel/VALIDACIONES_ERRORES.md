# Validaciones y errores

## Orden de validación

1. Confirmación sintética, nombre, extensión y tamaño.
2. Contenedor ZIP/OOXML, partes permitidas y límites expandidos.
3. Hojas `DATOS` y `META`, marca sintética e identidad de plantilla.
4. Encabezados exactos y ordenados.
5. Fórmulas y columnas adicionales.
6. Obligatoriedad y tipos.
7. Patrones, longitudes, catálogos, rangos y fechas futuras.
8. Datos reales evidentes y duplicados de fila o clave.
9. Hash del archivo contra cargas aceptadas/procesadas.

## Evidencia del error

Cada error incluye código estable, fila de Excel, columna, severidad, mensaje genérico y acción sugerida. El mensaje no copia el valor rechazado, de modo que una detección de información insegura no la replica en logs ni diagnóstico.

Los errores globales usan una fila técnica 0 con `raw_data={}`. Esta convención conserva la relación obligatoria ENT-020→ENT-021 sin inventar una fila funcional.

## Reintento

La corrección genera otro `ImportJob` con `retry_of_id` y `attempt_count` incrementado. El archivo, hash, errores y estado anteriores permanecen inmutables. Reenviar un archivo ya aceptado produce `duplicate` y `duplicate_of_id`, no un segundo conjunto procesable.
