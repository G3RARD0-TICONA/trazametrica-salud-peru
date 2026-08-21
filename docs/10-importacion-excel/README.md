# P10 — Importación Excel y calidad de datos

**Estado:** aprobada internamente  
**Puerta:** G10 cerrada — 12/12 controles conformes  
**Versión:** 1.0  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Implementar RF-010–014, CU-06–07, RN-007–010, RNF-007 y ENT-017–021: plantillas Excel versionadas, cargas identificadas, validación reproducible, staging, rechazo atómico, errores accionables, prevención de duplicados y reintentos trazables.

## 2. Alcance implementado

- Plantillas por organización, código, destino y versión.
- Esquema JSON normalizado con SHA-256 e historial inmutable.
- Publicación independiente: autor distinto del aprobador.
- Generación determinista de archivos `.xlsx` identificados en una hoja META protegida por contrato.
- Registro del archivo, plantilla, SHA-256, actor, fecha, intento y estado.
- Validación de estructura, encabezados, orden, tipos, obligatoriedad, patrones, fechas, rangos, catálogos y duplicados.
- Rechazo de macros, fórmulas, vínculos externos, objetos incrustados y archivos comprimidos inseguros.
- Marca `DATOS SINTÉTICOS` y bloqueo preventivo de columnas clínicas o datos personales evidentes.
- Filas de staging y errores con fila, columna, regla, mensaje y acción sugerida.
- Rechazo completo ante cualquier error bloqueante; ninguna fila pasa al conjunto procesado.
- Detección de archivo aceptado duplicado y relación con su antecedente.
- Reintentos numerados sin sobrescribir intentos anteriores.
- Promoción de una carga aceptada mediante `imports.review`.
- Catálogo, descarga, carga y detalle protegidos por `imports.create`.

## 3. Límites

- P10 procesa únicamente `.xlsx` sintéticos de hasta 10 MiB, 100 columnas y 10 000 filas.
- Las fechas se ingresan como texto ISO `AAAA-MM-DD`; las columnas de la plantilla se formatean como texto para evitar conversiones implícitas de Excel.
- El binario se valida durante la solicitud y `FileAsset` conserva sus metadatos; almacenamiento privado persistente, limpieza de huérfanos y recuperación tras interrupción se completarán en P17/P18.
- El staging aceptado queda disponible para P11; P10 no calcula ni publica KPI.
- La ejecución web usa el mismo servicio transaccional que podrá invocar el worker único; la cola distribuida no forma parte del MVP actual.
- No se autoriza uso productivo ni carga de información real.

## 4. Expediente

- [Modelo de importación](MODELO_IMPORTACION.md)
- [Contrato de plantillas](CONTRATO_PLANTILLAS.md)
- [Validaciones y errores](VALIDACIONES_ERRORES.md)
- [Seguridad XLSX](SEGURIDAD_XLSX.md)
- [Semilla y rendimiento](SEMILLA_RENDIMIENTO.md)
- [Trazabilidad, pruebas y puerta G10](TRAZABILIDAD_G10.md)

## 5. Resultado actual

Las verificaciones locales aprobaron 88 pruebas aplicables con 85 % de cobertura. Las CI #42 y #43 aprobaron las 89 pruebas en Python 3.13 y PostgreSQL 17, el contenedor, documentación, lint, tipado, migraciones, seguridad estática y auditoría de dependencias. El titular autorizó expresamente el cierre el 20 de agosto de 2026; G10 queda cerrada con 12/12 controles conformes.
