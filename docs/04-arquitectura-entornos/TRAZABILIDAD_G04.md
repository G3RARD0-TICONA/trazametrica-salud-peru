# Trazabilidad y puerta G04

## 1. P03 hacia arquitectura

| Requisitos P03 | Decisión/módulo | Verificación futura |
|---|---|---|
| RF-001–005 | `accounts`, `organizations`, ADR-008 | Permisos, desactivación y restricciones |
| RF-006–009 | `processes`, `documents` | Versiones, transiciones y autoaprobación bloqueada |
| RF-010–014 | `imports`, worker y staging | Atomicidad, hash, errores y recuperación |
| RF-015–018 | `indicators`, fórmula declarativa | Reproducibilidad y publicación versionada |
| RF-019–024 | `audits`, `improvements` | Flujo auditoría–hallazgo–acción–cierre |
| RF-025–027 | almacenamiento privado, `auditlog` | Hash, autorización y append-only funcional |
| RF-028–032 | `reports`, contratos y semillas | Filtros, exportación y restablecimiento |
| RF-033–035 | `risks` | Evaluación, vínculos, controles y alertas |
| RNF-001–005 | seguridad, transacciones y servicios | Pruebas negativas, rollback y determinismo |
| RNF-006–007 | PostgreSQL y conjunto de referencia | Rendimiento documentado en P17 |
| RNF-008 | HTML de servidor y accesibilidad | Auditoría WCAG en P17 |
| RNF-009–014 | Compose, CI, logs, zona y contratos | Instalación, recuperación y esquema |

## 2. Pruebas de aceptación arquitectónica

| ID | Verificación | Resultado esperado |
|---|---|---|
| PA-04-01 | Inspeccionar dependencias entre módulos | Sin ciclos ni imports de presentación cruzados |
| PA-04-02 | Ejecutar configuración local desde cero | Servicios saludables con un procedimiento documentado |
| PA-04-03 | Ejecutar suite contra PostgreSQL | No se usa SQLite ni fallback silencioso |
| PA-04-04 | Interrumpir worker durante un trabajo | Trabajo recuperable y sin promoción parcial |
| PA-04-05 | Invocar servicio sin permiso | Denegación antes de mutar datos |
| PA-04-06 | Aprobar dentro de transacción fallida | Datos y bitácora funcional se revierten coherentemente |
| PA-04-07 | Descargar evidencia sin permiso | Acceso denegado; archivo no tiene URL pública |
| PA-04-08 | Registrar fórmula con código dinámico | Expresión rechazada |
| PA-04-09 | Ejecutar `check --deploy` en demo | Sin advertencias críticas no justificadas |
| PA-04-10 | Analizar repositorio y logs | Sin secretos ni contenido sensible |
| PA-04-11 | Crear modelo sin migración | CI bloquea el cambio |
| PA-04-12 | Romper contrato de exportación | Prueba de esquema bloquea integración |
| PA-04-13 | Restaurar backup de demo | Base, manifiesto y archivos coherentes |
| PA-04-14 | Construir imagen desde commit y lock | Resultado reproducible y trazable |
| PA-04-15 | Revisar página crítica sin JavaScript | Operación principal continúa disponible |

## 3. Riesgos abiertos

| Riesgo | Tratamiento | Responsable posterior |
|---|---|---|
| Worker propio pierde trabajo | Estado persistente, bloqueo, intentos y prueba de interrupción | P10/P17 |
| Módulos se acoplan | Reglas de importación y servicios públicos | Construcción/P17 |
| Archivos y DB divergen | Manifiesto, transacción compensatoria y prueba de restauración | P05/P17 |
| Fórmula demasiado limitada | Catálogo versionado y casos reales sintéticos | P11 |
| Dependencias quedan obsoletas | Revisión mensual y CI de seguridad | Todas las versiones |
| Demo se confunde con producto clínico | Marca sintética y límites visibles | P18 |

## 4. Puerta G04

| N.º | Criterio | Estado |
|---:|---|---|
| 1 | Estilo arquitectónico elegido y justificado | Conforme |
| 2 | Versiones base compatibles y con soporte verificable | Conforme |
| 3 | Módulos, responsabilidades y dependencias definidos | Conforme |
| 4 | Capas y fronteras de transacción establecidas | Conforme |
| 5 | Flujo de importación y procesamiento definido | Conforme |
| 6 | Entornos local, test, CI y demo separados | Conforme |
| 7 | Configuración, secretos y archivos gobernados | Conforme |
| 8 | Controles de seguridad y amenazas documentados | Conforme |
| 9 | Estrategia de pruebas y CI definida | Conforme |
| 10 | P03 trazada a módulos y verificaciones | Conforme |
| 11 | Riesgos y decisiones diferidas asignados | Conforme |
| 12 | Aprobación interna del titular registrada | Conforme |

**Resultado final:** 12/12 controles conformes. El titular aceptó las 14 ADR y aprobó internamente P04/G04 el 20 de agosto de 2026.

## 5. Efecto de aprobación

El cierre de G04 permite elaborar P05 y crear el esqueleto técnico mínimo en una rama posterior. No autoriza datos reales, despliegue productivo, integraciones clínicas ni omitir las puertas de datos, permisos y pruebas.
