# Trazabilidad y puerta G06

## 1. Requisitos cubiertos

| Requisito P03 | Evidencia P06 | Prueba |
|---|---|---|
| RF-001 autenticación | Login/logout Django y usuario personalizado | redirección, login e inactividad |
| RF-002 autorización | Política, decorador y denegación por defecto | usuario sin rol = 403 |
| RF-003 administración de usuarios | Actor obligatorio y desactivación trazable | creación sin actor y desactivación |
| RF-004 roles y permisos | Ocho roles, 33 capacidades y vigencias | catálogo, rol vigente/expirado |
| RN-SEG-001 mínimo privilegio | Matriz explícita | comparación administrador/aprobador |
| RN-SEG-002 separación de funciones | Aprobaciones reservadas a `APPROVER` | prueba unitaria de segregación |
| RN-AUD-001 actor y fecha | Campos de auditoría y motivos | constraints y servicios |

## 2. Pruebas automatizadas

| Grupo | Cobertura esperada |
|---|---|
| Política | Catálogo de roles, segregación y límites temporales |
| Autenticación | Anónimo, cuenta activa, cuenta inactiva y rol expirado |
| Autorización | Panel, perfil y respuesta 403 sin capacidad |
| Servicios | Asignación, superposición, finalización y privilegio insuficiente |
| Integridad | Fecha invertida rechazada por PostgreSQL |
| Bootstrap | Cuenta técnica, ocho roles y asignación administrativa |
| Operación | Vida y disponibilidad con conexión PostgreSQL |

La cobertura mínima obligatoria es 80 % sobre `accounts` y `core`, excluyendo migraciones, administración y configuración declarativa de aplicaciones.

## 3. Controles de CI

1. Validación de Markdown y enlaces locales.
2. Ruff sobre código, pruebas y scripts.
3. Mypy con plugin de Django.
4. `manage.py check` y detección de migraciones faltantes.
5. Migración limpia sobre PostgreSQL 17.11.
6. Pytest y cobertura mínima de 80 %.
7. Bandit sobre el código fuente.
8. `pip-audit` sobre dependencias de producción.
9. Construcción del contenedor.

## 4. Evaluación de G06

| # | Criterio | Evidencia | Estado |
|---:|---|---|---|
| 1 | Arquitectura y versiones respetadas | Configuración, dependencias y contenedores | Conforme |
| 2 | Usuario personalizado en migración inicial | `AUTH_USER_MODEL` y `0001_initial` | Conforme |
| 3 | Identidad trazable y sin borrado funcional | Modelos y restricciones | Conforme |
| 4 | Ocho roles y matriz reproducible | Política y matriz | Conforme |
| 5 | Vigencias y superposición controladas | Servicio y constraint | Conforme |
| 6 | Autenticación e inactividad verificadas | Backend y pruebas | Conforme |
| 7 | Autorización en servidor | Decorador y pruebas HTTP | Conforme |
| 8 | Separación administración/aprobación | Política y prueba unitaria | Conforme |
| 9 | Arranque y bootstrap reproducibles | Compose, comando y guía | Conforme |
| 10 | Pruebas y controles definidos | Suite y workflow | Conforme |
| 11 | CI en Python 3.13.15/PostgreSQL 17.11 | GitHub Actions | Pendiente |
| 12 | Aceptación formal del titular | Decisión posterior a CI | Pendiente |

**Resultado actual:** 10/12. P06 está **EN PRUEBAS** y G06 permanece abierta. La aprobación solo procederá si CI finaliza conforme y el titular acepta el incremento; tampoco implica certificación, seguridad productiva ni autorización sanitaria.
