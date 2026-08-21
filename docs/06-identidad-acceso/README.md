# P06 — Identidad, autenticación, roles y permisos

**Estado:** aprobada internamente  
**Puerta:** G06 cerrada — 12/12 controles conformes  
**Versión:** 1.0  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Implementar el primer incremento ejecutable de Trazamétrica Salud Perú: configuración Django/PostgreSQL, usuario personalizado, autenticación por sesión, roles con vigencia, capacidades verificadas en el servidor y controles mínimos de seguridad. El incremento usa exclusivamente identidades y datos sintéticos.

## 2. Alcance implementado

- Python 3.13, Django 5.2 LTS y PostgreSQL 17 fijados por versión.
- Contenedores de aplicación y base de datos para ejecución reproducible.
- Usuario personalizado con UUID, actor creador/modificador y desactivación justificada.
- Ocho roles y 33 capacidades definidas en política explícita.
- Asignaciones de rol con fecha inicial, fecha final opcional y bloqueo de superposición.
- Inicio y cierre de sesión con controles nativos de Django.
- Autorización mediante decorador ejecutado en servidor; ocultar una opción visual no concede acceso.
- Separación entre administración técnica y aprobación funcional.
- Comando idempotente de bootstrap limitado a `local`, `test` y `demo`.
- Endpoints de vida y disponibilidad.
- Pruebas unitarias e integrales sobre PostgreSQL, cobertura, análisis estático, auditoría de dependencias y compilación del contenedor en CI.

## 3. Límites

- No hay autoservicio de registro, recuperación por correo, MFA, SSO ni federación.
- No se implementan todavía permisos por objeto o sede; las reglas actuales son capacidades globales y vigencias.
- No se cargan usuarios, correos, contraseñas ni datos clínicos reales.
- Las tablas internas de Django no incrementan las 46 entidades de dominio aprobadas en P05.
- El módulo no está autorizado para producción clínica.

## 4. Expediente

- [Modelo de identidad y acceso](MODELO_ACCESO.md)
- [Matriz de roles y capacidades](MATRIZ_PERMISOS.md)
- [Ejecución local y demostrativa](EJECUCION.md)
- [Trazabilidad, pruebas y puerta G06](TRAZABILIDAD_G06.md)

## 5. Base oficial

- Django exige configurar el [modelo de usuario personalizado antes de la primera migración](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/).
- El backend predeterminado impide la autenticación de [usuarios inactivos](https://docs.djangoproject.com/en/5.2/ref/contrib/auth/).
- Las sesiones y contraseñas usan las [capacidades de autenticación de Django](https://docs.djangoproject.com/en/5.2/topics/auth/default/).
- Django 5.2 es LTS y su mantenimiento se publica en la [página oficial de versiones](https://www.djangoproject.com/download/).

## 6. Resultado aprobado

GitHub Actions ejecutó conforme la matriz completa en Python 3.13.15 y PostgreSQL 17.11: 18 pruebas aprobadas, cobertura de 87 %, migraciones coherentes, análisis estático y de seguridad conformes, dependencias sin vulnerabilidades conocidas y contenedor construido. El titular autorizó el cierre el 20 de agosto de 2026; por ello G06 quedó cerrada con 12/12 controles. Esta aprobación interna no equivale a aptitud productiva, certificación ni autorización sanitaria.
