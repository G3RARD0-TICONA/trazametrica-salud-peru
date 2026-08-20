# Actores, responsabilidades y permisos

## 1. Actores

| ID | Actor | Responsabilidad principal | Restricción crítica |
|---|---|---|---|
| A01 | Administrador del sistema | Usuarios, roles, catálogos técnicos y configuración | No aprueba contenido por ser administrador |
| A02 | Responsable de calidad | Gobierno documental, auditorías, no conformidades y mejora | No cierra una acción propia sin segunda aprobación |
| A03 | Responsable de proceso | Procesos, riesgos, metas y acciones de su ámbito | No aprueba su propia versión de proceso |
| A04 | Analista de indicadores | Fichas KPI, cargas, cálculo, análisis y propuestas de publicación | No altera datos fuente ya aceptados |
| A05 | Cargador de datos | Importación y corrección de archivos sintéticos | No publica resultados ni modifica fórmulas |
| A06 | Auditor | Planes, listas de verificación, ejecución y hallazgos | No cierra sus propios hallazgos |
| A07 | Aprobador | Aprueba versiones, resultados y cierres dentro de su competencia | Debe ser distinto del autor del cambio |
| A08 | Consulta | Visualización y exportación autorizada | Sin creación, modificación, aprobación o anulación |
| A09 | Servicio interno | Validación, cálculo, alertas y bitácora automatizada | No actúa sin regla, versión y actor iniciador trazables |

No existe actor Paciente, Profesional clínico, Aseguradora o Autoridad sanitaria dentro del MVP.

## 2. Matriz de permisos de alto nivel

Leyenda: `C` crear, `E` editar, `R` revisar, `A` aprobar, `V` visualizar, `X` exportar y `—` sin permiso.

| Área | A01 | A02 | A03 | A04 | A05 | A06 | A07 | A08 |
|---|---|---|---|---|---|---|---|---|
| Usuarios y roles | C/E/V | V | V | V | V | V | V | — |
| Organización, sedes y servicios | C/E/V | R/V | R/V | V | V | V | A/V | V |
| Procesos y documentos | V | C/E/R/V | C/E/R/V | V | V | R/V | A/V | V |
| Fichas de indicadores | V | R/V | R/V | C/E/R/V | V | V | A/V | V |
| Importaciones | V | R/V | V | C/E/R/V | C/E/V | V | A/V | V |
| Auditorías y hallazgos | V | C/E/R/V | R/V | V | V | C/E/R/V | A/V | V |
| Acciones correctivas | V | C/E/R/V | C/E/R/V | V | V | R/V | A/V | V |
| Riesgos y controles | V | C/E/R/V | C/E/R/V | R/V | V | R/V | A/V | V |
| Bitácora | V/X | V/X | V | V | V | V | V/X | — |
| Reportes y exportaciones | V/X | V/X | V/X | V/X | V | V/X | V/X | V/X |

La matriz es una política base; P06 deberá convertirla en permisos granulares y probar denegaciones explícitas.

## 3. Segregación de funciones

1. El autor de una versión no puede aprobar esa misma versión.
2. El cargador no puede publicar un indicador.
3. El auditor no puede cerrar el hallazgo que registró.
4. El responsable de una acción no puede aprobar su propio cierre.
5. El administrador configura acceso, pero no obtiene aprobación funcional automática.
6. Toda excepción requiere motivo, actor autorizado y evento de bitácora; el MVP no contempla excepciones silenciosas.

## 4. Ciclo de acceso

- Un usuario nuevo inicia inactivo y sin permisos funcionales.
- A01 asigna roles; A07 o el titular valida los roles de aprobación.
- La desactivación bloquea nuevos accesos y conserva la autoría histórica.
- Los permisos se evalúan en el servidor para cada operación; ocultar un botón no constituye control suficiente.
