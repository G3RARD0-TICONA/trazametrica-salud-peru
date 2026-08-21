# Hallazgos, no conformidades y evidencia

## Registro RN-014

Un hallazgo requiere:

- ejecución y, cuando existe, respuesta exacta de origen;
- código, tipo, criterio y condición;
- impacto, responsable activo y vencimiento;
- uno o más archivos sintéticos limpios, o motivo explícito de ausencia.

La validación ocurre antes de guardar. Si una evidencia es rechazada, real, insegura o carece de descripción, la transacción completa se revierte.

## Clasificación

| Campo | Valores |
|---|---|
| Tipo | observación, oportunidad de mejora, no conformidad |
| Impacto | bajo, medio, alto, crítico |
| Estado P12 | abierto, en análisis, cancelado |
| Alerta | vencido, próximo en 7 días, en plazo, no aplicable |

## Evidencia

`FindingEvidence` reutiliza `FileAsset`; conserva nombre seguro, tipo, tamaño, SHA-256, escaneo y confirmación sintética. Los binarios permanecen fuera del repositorio y la interfaz muestra solo metadatos autorizados.

## Cancelación

Una cancelación exige permiso de revisión y motivo. No elimina la fila ni su evidencia. El cierre por eficacia no existe en P12 y no puede simularse cambiando el estado manualmente.
