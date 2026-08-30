# Registro de cambios

Este proyecto sigue [Versionado Semántico](https://semver.org/lang/es/) desde el primer incremento ejecutable. Los cambios todavía no publicados se registran bajo `Sin publicar`.

## Sin publicar

### Añadido

- P17 en pruebas con regresión integral, seguridad transversal, rendimiento de referencia, accesibilidad WCAG 2.2 AA y manifiesto de recuperación.
- Argon2, CSP, política de permisos, correlación de solicitudes, caché privada y bitácora de autorizaciones denegadas.
- Puertas CI de repositorio seguro, `check --deploy`, accesibilidad estructural, p95, presupuestos SQL y conjunto de 100 000 observaciones.
- CI #75 conforme para P17 con 170 pruebas en PostgreSQL 17, 82 % de cobertura, seguridad, dependencias, accesibilidad, rendimiento e imagen aprobados.

- P16 con estadística descriptiva, atípicos, Pareto, gráficos de control, medias móviles, regresión lineal y logística reproducibles.
- Definiciones analíticas versionadas, ejecuciones inmutables, separación cronológica entrenamiento/prueba, métricas, supuestos, líneas base y hashes SHA-256.
- CI #71 conforme para P16 con 163 pruebas en PostgreSQL 17, 82 % de cobertura y controles de seguridad, dependencias e imagen aprobados.
- P16 aprobada internamente y G16 cerrada con 12/12 controles tras la aceptación formal del titular del 30 de agosto de 2026.

- P15 con tablero KPI filtrable, contratos de exportación versionados, CSV/XLSX/PDF auditables, conjunto estable para Power BI Desktop y semilla sintética determinista.
- CI #67 y #68 conformes para P15 con 151 pruebas en PostgreSQL 17, 82 % de cobertura y controles de seguridad y dependencias aprobados.
- P15 aprobada internamente y G15 cerrada con 12/12 controles tras la aceptación formal del titular del 29 de agosto de 2026.

- Identidad pública de Trazamétrica Salud Perú.
- Alcance, exclusiones, estado modular y tecnología prevista.
- Aviso de derechos para un repositorio público sin licencia.
- Política de seguridad y prohibición de datos reales.
- Expedientes resumidos P00 y P01.
- Matriz auditable de P02 y puerta G02 aprobada.
- Expediente P03 de actores, requisitos, reglas, casos de uso y trazabilidad aprobado.
- Expediente P04 de arquitectura, entornos, seguridad, calidad y 14 decisiones técnicas aceptado; G04 aprobada con 12/12 controles conformes.
- Expediente P05 de modelo de dominio, diccionario físico, integridad, índices, migraciones y semillas sintéticas aprobado; G05 cerrada con 12/12 controles conformes.
- Roadmap de P00 a P18.
- Base ejecutable P06 con Django 5.2 LTS, PostgreSQL 17, Docker Compose y GitHub Actions.
- Usuario personalizado, ocho roles, 33 capacidades, vigencias, segregación de funciones y autorización en servidor.
- Pruebas unitarias e integrales, controles de calidad, endpoints de salud y bootstrap sintético.
- Expediente P06 aprobado y puerta G06 cerrada con 12/12 controles conformes.
- Maestros P07 de organización, sedes, servicios, áreas y responsabilidades con migración PostgreSQL.
- Semilla organizacional determinista, vista protegida y pruebas de integridad/autorización.
- CI de P07 conforme con 36 pruebas, 86 % de cobertura, seguridad y dependencias sin hallazgos, y contenedor reproducible.
- Expediente P07 aprobado y puerta G07 cerrada con 12/12 controles conformes.
- Dominio P08 de documentos, versiones, archivos sintéticos y fuentes de referencia.
- Flujo transaccional de revisión, aprobación independiente, sustitución, anulación y desactivación.
- Bitácora append-only ENT-046, hashes de integridad y catálogo protegido por `documents.view`.
- Migraciones y pruebas P08 para integridad, autorización, vigencia, inmutabilidad y seguridad documental.
- CI de P08 conforme con 56 pruebas, 86 % de cobertura, seguridad y dependencias sin hallazgos, y contenedor reproducible.
- Expediente P08 aprobado internamente y puerta G08 cerrada con 12/12 controles conformes.
- Dominio P09 de procesos, versiones y elementos SIPOC con integridad relacional.
- Flujo transaccional de borrador, revisión, aprobación independiente, vigencia, sustitución, anulación y desactivación.
- Fichas de proceso con objetivo, alcance y las cinco secciones SIPOC obligatorias antes de revisión.
- Relación documental `Document.process`, catálogo protegido y semilla determinista de 100 procesos y 500 elementos SIPOC.
- Migraciones y 11 pruebas nuevas para autorización, integridad, inmutabilidad, vigencia, vínculo documental y semilla sintética.
- CI de P09 conforme con 68 pruebas, 86 % de cobertura, seguridad y dependencias sin hallazgos, y contenedor reproducible.
- Expediente P09 aprobado internamente y puerta G09 cerrada con 12/12 controles conformes.
- Dominio P10 de plantillas, versiones, cargas, filas de staging y errores accionables.
- Adaptador OOXML seguro y sustituible para generar y leer XLSX sin macros, fórmulas ni vínculos externos.
- Validación de identidad de plantilla, encabezados, tipos, obligatoriedad, códigos, fechas, rangos, catálogos, duplicados y datos inseguros.
- Rechazo atómico, SHA-256 de archivo y filas, antecedente duplicado, reintentos y promoción controlada.
- Cuatro plantillas sintéticas deterministas, interfaz protegida y prueba de referencia de 10 000 filas.
- CI #42 de P10 conforme con 89 pruebas, 85 % de cobertura, seguridad y dependencias sin hallazgos, y contenedor reproducible.
- CI final #43 conforme sobre el commit de evidencia de P10.
- Expediente P10 aprobado internamente y puerta G10 cerrada con 12/12 controles conformes mediante autorización expresa del titular.
- Dominio P11 de indicadores, fichas versionadas, observaciones, resultados y entradas trazables.
- Motor declarativo decimal con operadores permitidos, límites estructurales, SHA-256 y prohibición de evaluación dinámica.
- Materialización atómica desde cargas P10 procesadas y validación de periodo, sede, servicio y dimensión.
- Flujo de cálculo, revisión, rechazo, publicación y corrección sin sobrescribir resultados publicados.
- Estado automático de desempeño según meta, umbral y sentido del KPI.
- Catálogo protegido y semilla determinista de 200 KPI, 260 fichas y hasta 100 000 observaciones sintéticas.
- Expediente P11 aprobado internamente y puerta G11 cerrada con 12/12 controles conformes mediante autorización expresa del titular.
- CI #48 de P11 conforme con 104 pruebas sobre PostgreSQL 17, 83 % de cobertura, seguridad y dependencias sin hallazgos, y contenedor reproducible.
- CI #49 conforme sobre el commit de evidencia de P11 y CI final #50 conforme sobre su cierre G11.
- Dominio P12 de planes, listas versionadas, criterios, ejecuciones, respuestas, hallazgos y evidencias.
- Flujos segregados de planificación, aprobación, ejecución, devolución y término de auditoría.
- RN-014 implementada mediante evidencia sintética validada o justificación expresa de ausencia.
- Bloqueo de ejecución incompleta y de no conformidad sin hallazgo trazable.
- Alertas de vencimiento, catálogo protegido y semilla determinista de 12 planes y 180 hallazgos.
- CI #52 y #53 de P12 conformes con 115 pruebas sobre PostgreSQL 17, 83 % de cobertura, seguridad y dependencias sin hallazgos, y contenedor reproducible.
- Expediente P12 aprobado internamente y puerta G12 cerrada con 12/12 controles conformes mediante autorización expresa del titular.
- CI final #54 conforme sobre el cierre G12 y la integración de P12.
- Dominio P13 de causa raíz, acciones correctivas, evidencias y revisión de eficacia.
- Flujo segregado de causa, aprobación del plan, ejecución, verificación, cierre y reapertura.
- RN-015–019 implementadas con atomicidad, reasignación trazable y cierre condicionado.
- Alertas de vencimiento y responsable inactivo, catálogo protegido y semilla determinista 12/24/18/15.
- CI #56 y #57 de P13 conformes con 125 pruebas sobre PostgreSQL 17, 83 % de cobertura, seguridad y dependencias sin hallazgos, y contenedor reproducible.
- Expediente P13 aprobado internamente y puerta G13 cerrada con 12/12 controles conformes mediante autorización expresa del titular.
- Dominio P14 de riesgos por proceso, evaluaciones inherentes/residuales, controles versionados y revisiones independientes.
- Matriz 5×5 reproducible, alertas derivadas, vínculos explícitos con KPI, hallazgos y acciones, aceptación residual y cierre condicionado.
- Catálogo protegido y semilla determinista de 20 riesgos, 24 evaluaciones, 12 controles, 24 asignaciones y 18 revisiones con datos sintéticos.
- CI #61 de P14 conforme con 140 pruebas sobre PostgreSQL 17, 82 % de cobertura, seguridad y dependencias sin hallazgos, y contenedor reproducible.
- CI #62 conforme sobre el expediente técnico final de P14.
- Expediente P14 aprobado internamente y puerta G14 cerrada con 12/12 controles conformes mediante autorización expresa del titular.

### Pendiente

- Implementación de P18.
