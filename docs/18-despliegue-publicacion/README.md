# P18 — Despliegue demostrativo, manuales y publicación final

**Estado:** en pruebas

**Puerta:** G18 abierta — 11/12 controles conformes; simulacro externo y aceptación pendientes

**Versión:** 1.0-rc.1

**Fecha de corte:** 30 de agosto de 2026

## Objetivo

Dejar una demostración reproducible de Trazamétrica Salud Perú lista para publicar bajo control del titular: contenedor WSGI, proxy TLS, PostgreSQL 17 aislado, operación, recuperación, manual de usuario y procedimiento de release.

## Alcance implementado

- imagen no privilegiada con Gunicorn, comprobación de despliegue, migraciones y estáticos;
- `compose.demo.yaml` con PostgreSQL 17 sin puertos públicos, volumen privado y proxy Caddy;
- TLS automático cuando `DEMO_CADDY_ADDRESS` contiene un FQDN propio; simulacro local por HTTP aislado;
- sondas `/health/live/` y `/health/ready/` sin caché ni secretos;
- aviso visible de **DEMO PÚBLICA — DATOS SINTÉTICOS** en la aplicación;
- manuales de operación, recuperación, usuario y publicación final;
- contrato automatizado de despliegue en CI.

## Límites

P18 publica únicamente una demo administrativa y no clínica. No habilita pacientes reales, historias clínicas, credenciales compartidas, certificados, afiliación con clínicas ni disponibilidad productiva. La activación de un proveedor, un dominio y sus secretos la realiza exclusivamente el titular en su propia cuenta.

## Expediente

- [Arquitectura y despliegue demostrativo](ARQUITECTURA_DEMO.md)
- [Manual de operación](MANUAL_OPERACION.md)
- [Manual de usuario](MANUAL_USUARIO.md)
- [Recuperación operativa](RECUPERACION_OPERATIVA.md)
- [Publicación final](PUBLICACION_FINAL.md)
- [Trazabilidad y puerta G18](TRAZABILIDAD_G18.md)

## Resultado actual

La CI #79 aprobó 172 pruebas sobre PostgreSQL 17, 82 % de cobertura, documentación, lint, tipado, migraciones, seguridad, contrato de despliegue, accesibilidad, Bandit, dependencias e imagen. Antes de declarar la publicación final se exige que el titular ejecute el simulacro sobre un proveedor y dominio que controle, y que registre la aceptación formal.
