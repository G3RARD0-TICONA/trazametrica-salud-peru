# Matriz de roles y capacidades

## 1. Roles

| Código | Función demostrativa | Puede aprobar |
|---|---|---|
| `ADMIN_SYSTEM` | Cuentas, roles, organización técnica y consulta de bitácora | No |
| `QUALITY_MANAGER` | Procesos, documentos, auditorías, mejoras, riesgos y analítica | No |
| `PROCESS_OWNER` | Elaboración y seguimiento de procesos asignados | No |
| `INDICATOR_ANALYST` | Cargas, indicadores, reportes y analítica | No |
| `DATA_LOADER` | Preparación y envío de cargas | No |
| `AUDITOR` | Ejecución/revisión de auditorías y evidencias | No |
| `APPROVER` | Aprobaciones independientes y publicación | Sí |
| `VIEWER` | Consulta y exportación permitida | No |

## 2. Capacidades por área

`✓` indica concesión explícita. Una celda vacía significa denegación.

| Capacidad | ADM | CAL | PRO | KPI | CAR | AUD | APR | LEC |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Ver panel | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Gestionar usuarios | ✓ |  |  |  |  |  |  |  |
| Asignar roles | ✓ |  |  |  |  |  |  |  |
| Aprobar acceso |  |  |  |  |  |  | ✓ |  |
| Gestionar organización | ✓ |  |  |  |  |  |  |  |
| Ver organización | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Elaborar procesos |  | ✓ | ✓ |  |  |  |  |  |
| Revisar procesos |  | ✓ | ✓ |  |  |  |  |  |
| Aprobar procesos |  |  |  |  |  |  | ✓ |  |
| Ver procesos |  | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Gestionar documentos |  | ✓ | ✓ |  |  |  |  |  |
| Revisar documentos |  | ✓ |  |  |  |  |  |  |
| Aprobar documentos |  |  |  |  |  |  | ✓ |  |
| Ver documentos | ✓ | ✓ | ✓ |  |  | ✓ | ✓ | ✓ |
| Crear importaciones |  |  |  | ✓ | ✓ |  |  |  |
| Revisar importaciones |  |  |  | ✓ |  |  |  |  |
| Aprobar importaciones |  |  |  |  |  |  | ✓ |  |
| Elaborar indicadores |  |  |  | ✓ |  |  |  |  |
| Revisar indicadores |  |  |  | ✓ |  |  |  |  |
| Publicar indicadores |  |  |  |  |  |  | ✓ |  |
| Planificar auditorías |  | ✓ |  |  |  |  |  |  |
| Ejecutar auditorías |  |  |  |  |  | ✓ |  |  |
| Revisar auditorías |  | ✓ |  |  |  | ✓ |  |  |
| Aprobar auditorías |  |  |  |  |  |  | ✓ |  |
| Gestionar mejoras |  | ✓ | ✓ |  |  |  |  |  |
| Revisar mejoras |  | ✓ |  |  |  | ✓ |  |  |
| Aprobar mejoras |  |  |  |  |  |  | ✓ |  |
| Gestionar riesgos |  | ✓ | ✓ |  |  |  |  |  |
| Revisar riesgos |  | ✓ |  |  |  | ✓ |  |  |
| Aprobar riesgos |  |  |  |  |  |  | ✓ |  |
| Ver reportes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Exportar reportes |  | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Ver analítica | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Gestionar analítica |  | ✓ |  | ✓ |  |  |  |  |
| Aprobar analítica |  |  |  |  |  |  | ✓ |  |
| Ejecutar analítica |  | ✓ |  | ✓ |  |  |  |  |
| Ver bitácora | ✓ | ✓ |  |  |  |  | ✓ |  |
| Exportar bitácora |  |  |  |  |  |  | ✓ |  |

Abreviaturas: ADM administrador; CAL calidad; PRO responsable de proceso; KPI analista; CAR cargador; AUD auditor; APR aprobador; LEC consulta.

## 3. Interpretación

- El superusuario de bootstrap es una cuenta técnica de recuperación para entornos sintéticos; no representa un rol operativo y debe usarse solo para administración controlada.
- La matriz base de P06 tenía 33 capacidades. P08 añade `documents.view` como capacidad 34 y conserva separadas gestión, revisión, aprobación y consulta.
- P07 agrega comprobaciones de capacidad, estado y ámbito; P08 aplica además estado de versión, separación de autor/aprobador y ámbito organizacional.
- P16 añade capacidades separadas para consultar, gestionar, aprobar y ejecutar analítica; publicar conserva segregación entre autor y aprobador.
- Tener un rol no elimina reglas de negocio: por ejemplo, aprobar requiere además que el elemento esté en el estado correcto y que el aprobador no sea el autor cuando la separación aplique.
