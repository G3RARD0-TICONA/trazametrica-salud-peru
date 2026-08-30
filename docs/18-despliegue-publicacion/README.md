# P18 — Despliegue demostrativo, manuales y publicación final

**Estado:** aprobada internamente

**Puerta:** G18 cerrada — 12/12 controles conformes

**Versión:** 1.0

**Fecha de corte:** 30 de agosto de 2026

## Objetivo

Dejar una demostración reproducible y gratuita de Trazamétrica Salud Perú: contenedor WSGI, proxy local, PostgreSQL 17 aislado, operación, recuperación, manual de usuario y publicación final mediante GitHub Release.

## Alcance implementado

- imagen no privilegiada con Gunicorn, comprobación de despliegue, migraciones y estáticos;
- `compose.demo.yaml` con PostgreSQL 17 sin puertos públicos, volumen privado y proxy Caddy;
- ejecución local por `http://localhost:8080`, sin dominio, hosting ni tarjeta;
- sondas `/health/live/` y `/health/ready/` sin caché ni secretos;
- aviso visible de **DEMO PÚBLICA — DATOS SINTÉTICOS** en la aplicación;
- manuales de operación, recuperación, usuario y publicación final;
- contrato automatizado y arranque real del stack Docker en CI.

## Límites

P18 publica únicamente código y documentación de una demo administrativa y no clínica. GitHub no aloja la aplicación. No se habilitan pacientes reales, historias clínicas, credenciales compartidas, certificados, afiliación con clínicas ni disponibilidad productiva. La demo local no debe exponerse a Internet.

## Expediente

- [Arquitectura y despliegue demostrativo](ARQUITECTURA_DEMO.md)
- [Manual de operación](MANUAL_OPERACION.md)
- [Manual de usuario](MANUAL_USUARIO.md)
- [Recuperación operativa](RECUPERACION_OPERATIVA.md)
- [Publicación final](PUBLICACION_FINAL.md)
- [Trazabilidad y puerta G18](TRAZABILIDAD_G18.md)

## Resultado actual

Las CI #82 y #83 aprobaron 172 pruebas sobre PostgreSQL 17, 82 % de cobertura, documentación, lint, tipado, migraciones, seguridad, accesibilidad, Bandit y dependencias. También construyeron y levantaron PostgreSQL, Django/Gunicorn y Caddy mediante Docker Compose, comprobaron las dos sondas locales y eliminaron el entorno de prueba. La aceptación formal del titular autorizó el cierre, la integración y la GitHub Release `v0.1.0` el 30 de agosto de 2026.
