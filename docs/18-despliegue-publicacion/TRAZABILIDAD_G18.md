# Trazabilidad y puerta G18

## Controles G18

| N.° | Control | Evidencia | Estado |
|---:|---|---|---|
| 1 | Alcance demostrativo | límites visibles y expediente P18 | Conforme |
| 2 | WSGI no privilegiado | Dockerfile con Gunicorn y usuario `app` | Conforme |
| 3 | Proxy y aislamiento | Caddy; PostgreSQL sin puertos públicos | Conforme |
| 4 | TLS configurable | FQDN propio en `DEMO_CADDY_ADDRESS` | Conforme |
| 5 | Arranque verificable | `check --deploy`, migraciones y estáticos | Conforme |
| 6 | Salud y observabilidad segura | sondas sin caché y correlación | Conforme |
| 7 | Datos sintéticos visibles | banner, manual y política | Conforme |
| 8 | Operación documentada | manual de arranque, detención e incidentes | Conforme |
| 9 | Recuperación operativa | respaldo, manifiesto y restauración aislada | Conforme |
| 10 | Publicación trazable | procedimiento de tag y GitHub Release | Conforme |
| 11 | CI oficial P18 | CI #79: 172 pruebas, 82 %, contrato, seguridad, dependencias e imagen | Conforme |
| 12 | Simulacro externo y aceptación formal | URL del titular, TLS, evidencia y autorización | Pendiente |

**Resultado previo al simulacro externo:** 11/12 controles conformes. G18 permanece abierta. No se publica una URL, release ni dominio antes de un simulacro externo y aceptación expresa del titular.
