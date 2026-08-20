# P02 — Marco legal, normativo y referencias

**Estado:** aprobada internamente  
**Puerta:** G02 cerrada, 12/12 controles conformes  
**Fecha de corte:** 20 de agosto de 2026  
**Ámbito:** Perú; proyecto demostrativo público con datos sintéticos

## 1. Objetivo

Determinar qué normas condicionan el diseño, cuáles solo se activarían ante una implementación real y cuáles se utilizan como referencias voluntarias. El expediente traduce esa clasificación en controles verificables del producto y evita afirmaciones de cumplimiento que el proyecto no puede demostrar.

Este análisis es una base de diseño y no sustituye asesoría jurídica ni una evaluación de cumplimiento para una clínica concreta.

## 2. Regla de aplicabilidad

| Nivel | Significado |
|---|---|
| Directa al repositorio | Control obligatorio para publicar y desarrollar este proyecto |
| Condicional | Se activa si el sistema usa datos reales o se despliega en una organización de salud |
| Referencia | Orienta el diseño, pero no demuestra conformidad ni certificación |
| Fuera del MVP | Materia excluida de la primera versión |

## 3. Matriz de fuentes y decisiones

| ID | Fuente oficial | Nivel para el proyecto | Activador | Decisión de diseño |
|---|---|---|---|---|
| N01 | [Ley 26842, Ley General de Salud](https://www.gob.pe/institucion/minsa/normas-legales/256661-26842) | Condicional y referencia sectorial | Operación real de servicios de salud | El MVP no presta atención ni toma decisiones clínicas. |
| N02 | [DS 013-2006-SA, Reglamento de Establecimientos de Salud y Servicios Médicos de Apoyo](https://www.gob.pe/institucion/minsa/normas-legales/tipos/9-decreto-supremo?sheet=25) y modificaciones | Condicional | Despliegue en un establecimiento o servicio médico | Requerir evaluación institucional antes de producción; no modelar habilitación sanitaria como certificación propia. |
| N03 | [Ley 29414 y DS 027-2015-SA, derechos de las personas usuarias](https://www.gob.pe/institucion/minsa/normas-legales/997327-027-2015-sa) | Condicional | Interacción con usuarios o atención real | No registrar pacientes ni consentimientos clínicos en el MVP. |
| N04 | Ley 29733 y [DS 016-2024-JUS, Reglamento de Protección de Datos Personales](https://www.gob.pe/institucion/anpd/normas-legales/6554453-16-2024-jus) | Directa como prevención; condicional para tratamiento real | Incorporación de cualquier dato personal | Prohibición de datos reales, minimización, acceso por rol, manejo de incidentes y revisión previa de cada conjunto de datos. |
| N05 | [Ley 30024, Registro Nacional de Historias Clínicas Electrónicas](https://www.gob.pe/institucion/minsa/normas-legales/240527-30024) | Fuera del MVP; condicional | Historia clínica electrónica o integración con RENHICE | No crear historias clínicas ni interoperar con RENHICE. |
| N06 | [DS 009-2017-SA](https://www.gob.pe/institucion/minsa/normas-legales/190005-009-2017-sa), modificado por [DS 020-2025-SA](https://www.gob.pe/institucion/minsa/normas-legales/7479922-020-2025-sa) | Fuera del MVP; condicional | Intercambio de historias clínicas electrónicas | Registrar como dependencia futura bloqueante, no como funcionalidad demostrativa. |
| N07 | [RM 214-2018-MINSA, NTS 139 para la gestión de la historia clínica](https://www.gob.pe/institucion/minsa/normas-legales/187487-214-2018-minsa) | Fuera del MVP; referencia | Gestión documental clínica real | Distinguir documentos administrativos de historias clínicas. |
| N08 | [RM 519-2006-MINSA, Sistema de Gestión de la Calidad en Salud](https://www.gob.pe/institucion/minsa/normas-legales/251477) | Referencia | Diseño de procesos de calidad | Trazar procesos, medición, auditoría y mejora sin afirmar acreditación. |
| N09 | [RM 727-2009-MINSA, Política Nacional de Calidad en Salud](https://www.gob.pe/institucion/minsa/normas-legales/246122-727-2009-) | Referencia | Definición de criterios de calidad | Mantener calidad y mejora continua como propósito administrativo. |
| N10 | [ISO 7101:2023](https://www.iso.org/standard/81647.html) | Referencia voluntaria | Catálogo de requisitos y diseño del sistema de gestión | Usar procesos documentados, riesgos, desempeño y mejora; no declarar conformidad ni certificación. |

## 4. Requisitos convertidos en controles

| Control | Requisito verificable | Evidencia prevista |
|---|---|---|
| C02-01 | Solo datos sintéticos en repositorio, pruebas, demostraciones y capturas | Validador de datos, revisión de PR y etiqueta visible |
| C02-02 | No existe entidad Paciente, Historia clínica, Diagnóstico, Tratamiento o Receta en el MVP | Modelo de dominio y pruebas de esquema |
| C02-03 | Clasificación de datos por campo y archivo | Diccionario de datos con clase, finalidad y retención |
| C02-04 | Importaciones aisladas hasta superar estructura, tipo, tamaño y reglas de negocio | Registro de carga, errores y rechazo atómico |
| C02-05 | Permisos de mínimo privilegio y segregación entre registro, revisión y aprobación | Matriz de roles y pruebas de autorización |
| C02-06 | Bitácora de creación, modificación, aprobación, anulación y exportación | Eventos con actor, fecha, objeto, acción y resultado |
| C02-07 | Secretos fuera del repositorio y configuración por entorno | `.gitignore`, variables de entorno y análisis de secretos |
| C02-08 | Toda salida demostrativa indica `DATOS SINTÉTICOS` | Pruebas de exportación y revisión visual |
| C02-09 | Retención y eliminación configurables para datos administrativos | Política y pruebas de ciclo de vida |
| C02-10 | Incidentes con contención, revocación, evaluación y registro | Procedimiento y simulacro sin datos reales |
| C02-11 | Cada referencia conserva fuente, fecha de consulta, alcance y versión | Catálogo normativo versionado |
| C02-12 | Ninguna pantalla o documento afirma certificación, afiliación o aprobación | Revisión terminológica automatizada y manual |

## 5. Bloqueos para una futura implementación real

Antes de usar datos personales o desplegar el sistema en una clínica se deberá abrir una nueva evaluación que, como mínimo, determine roles legales, finalidad y base habilitante, consentimiento cuando corresponda, banco de datos, encargados y transferencias, medidas de seguridad, retención, atención de derechos, respuesta a incidentes, obligaciones sectoriales y contratos. Esa evaluación queda fuera del MVP público.

## 6. Criterios de aceptación G02

| N.º | Criterio | Estado |
|---:|---|---|
| 1 | Ámbito y fecha de corte identificados | Conforme |
| 2 | Fuentes oficiales enlazadas | Conforme |
| 3 | Aplicabilidad directa, condicional y referencial separada | Conforme |
| 4 | Datos personales y clínicos excluidos del MVP | Conforme |
| 5 | RENHICE e historia clínica fuera del MVP | Conforme |
| 6 | Controles técnicos trazados a riesgos | Conforme |
| 7 | Uso de ISO 7101 limitado a referencia | Conforme |
| 8 | Prohibición de afirmaciones de certificación o afiliación | Conforme |
| 9 | Bloqueos para producción real definidos | Conforme |
| 10 | Revisión periódica y responsable establecidos | Conforme |
| 11 | Descargo de asesoría jurídica declarado | Conforme |
| 12 | Aprobación interna del titular registrada | Conforme |

**Resultado:** 12/12 controles conformes. El titular aprobó expresamente la matriz y autorizó el cierre de G02 el 20 de agosto de 2026.

## 7. Mantenimiento

- Responsable: titular del producto.
- Revisión ordinaria: trimestral y antes de cada versión pública.
- Revisión extraordinaria: cambio de alcance, incorporación de datos reales, integración externa, despliegue institucional o cambio normativo relevante.
- Toda modificación debe registrar fuente, fecha, impacto, decisión, responsable y pruebas afectadas.
