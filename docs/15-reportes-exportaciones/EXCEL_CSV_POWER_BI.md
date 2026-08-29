# Excel, CSV y Power BI Desktop

## CSV

- UTF-8 con BOM para interoperabilidad local.
- Orden de columnas fijado por contrato.
- Escape RFC 4180 mediante el escritor CSV estándar.
- Prefijo seguro para texto que comienza con `=`, `+`, `-` o `@`.

## XLSX

La salida reutiliza el adaptador OOXML controlado de P10. Contiene hojas `DATOS`, `INSTRUCCIONES` y `META`; congela encabezados y no ejecuta macros, fórmulas ni enlaces externos.

## Power BI Desktop

`RPT-KPI-PBI-CSV` v1 publica el conjunto `indicator_results` como contrato estable. Power BI Desktop puede importar el CSV local por encabezados documentados. No se incluyen credenciales, gateway, actualización automática, Power BI Service ni publicación externa.

Una modificación de columnas, tipos u orden exige un contrato nuevo; el hash permite detectar cualquier diferencia antes de consumir el archivo.
