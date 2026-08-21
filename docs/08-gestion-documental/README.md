# P08 — Gestión documental y control de versiones

**Estado:** aprobada internamente  
**Puerta:** G08 cerrada — 12/12 controles conformes  
**Versión:** 1.0  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Implementar RF-008, RF-009, CU-05, CU-19 y las entidades ENT-012–ENT-016 de P05: documentos administrativos y fuentes de referencia con versiones, vigencia, revisión independiente, archivos sintéticos controlados, historial inmutable y trazabilidad de decisiones.

## 2. Alcance implementado

- Catálogo de documentos por organización y área responsable.
- Versiones consecutivas con contenido de texto o archivo, nunca ambos.
- Flujo `borrador → en revisión → aprobado/vigente → sustituido/anulado`.
- Separación obligatoria entre autor y aprobador.
- Rechazo, anulación y desactivación con motivo.
- Una sola vigencia no superpuesta por documento o referencia.
- Archivos con clave opaca, nombre seguro, MIME/extensión permitidos, tamaño, SHA-256, estado de escaneo y confirmación sintética.
- Fuentes legales, normativas o internas sin declarar certificación ni cumplimiento institucional.
- Bitácora ENT-046 append-only para operaciones documentales exitosas.
- Vista de catálogo protegida por la nueva capacidad `documents.view`.

## 3. Decisiones de implementación escalonada

P05 preveía `documents_document.process_id`, pero el modelo `Process` nace en P09. P08 no crea una dependencia circular ni un marcador sin integridad: añade `responsible_area_id` obligatorio para asignar responsabilidad real y deja `process_id` para la migración de P09. El diccionario P05 registra expresamente esta extensión.

ENT-046 estaba prevista para una parte posterior, pero P08 la introduce antes porque RF-009 exige una bitácora verificable desde la primera aprobación documental. La tabla es genérica y reutilizable por P09–P15.

## 4. Límites

- Solo se admiten datos y archivos sintéticos; no se procesan historias clínicas ni datos personales reales.
- El registro de archivo conserva metadatos y una clave de almacenamiento; el adaptador físico de almacenamiento y análisis antimalware productivo pertenece a P17/P18.
- La consulta web está implementada; las mutaciones se realizan mediante servicios de aplicación controlados. Los formularios operativos completos se incorporarán cuando se consolide la interfaz transversal.
- Una referencia organiza evidencia, pero no certifica ni garantiza cumplimiento legal, sanitario, ISO o JCI.
- No se autoriza uso productivo en una clínica.

## 5. Expediente

- [Modelo documental](MODELO_DOCUMENTAL.md)
- [Flujo de versiones](FLUJO_VERSIONES.md)
- [Archivos y seguridad](ARCHIVOS_SEGURIDAD.md)
- [Trazabilidad, pruebas y puerta G08](TRAZABILIDAD_G08.md)

## 6. Resultado aprobado

La ejecución #34 de GitHub Actions validó 56 pruebas en Python 3.13.15 y PostgreSQL 17.11, con 86 % de cobertura, cero hallazgos de Bandit, cero vulnerabilidades conocidas y construcción correcta del contenedor. El titular aceptó formalmente el resultado el 20 de agosto de 2026; por ello, P08 está aprobada internamente y G08 queda cerrada con 12/12 controles conformes.
