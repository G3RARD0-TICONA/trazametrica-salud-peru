# Trazabilidad y puerta G18

## Controles G18

| N.° | Control | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance demostrativo | límites visibles y expediente P18 | Conforme |
| 2 | WSGI no privilegiado | Dockerfile con Gunicorn y usuario `app` | Conforme |
| 3 | Proxy y aislamiento | Caddy; PostgreSQL sin puertos públicos | Conforme |
| 4 | Límite de red local | HTTP en `localhost`; sin dominio, túnel ni hosting | Conforme |
| 5 | Arranque verificable | `check --deploy`, migraciones y estáticos | Conforme |
| 6 | Salud y observabilidad segura | sondas sin caché y correlación | Conforme |
| 7 | Datos sintéticos visibles | banner, manual y política | Conforme |
| 8 | Operación documentada | manual de arranque, detención e incidentes | Conforme |
| 9 | Recuperación operativa | respaldo, manifiesto y restauración aislada | Conforme |
| 10 | Publicación trazable | procedimiento de tag y GitHub Release sin URL de aplicación | Conforme |
| 11 | Simulacro Docker oficial | CI #82: build, Compose, sondas y cierre limpio | Conforme |
| 12 | Aceptación formal | autorización expresa del titular del 30 de agosto de 2026 | Conforme |

**Resultado final:** 12/12 controles conformes. G18 queda cerrada y P18 aprobada internamente. El titular autorizó expresamente la integración del PR #17 y la publicación de la release `v0.1.0`; no se publica una URL de aplicación.
