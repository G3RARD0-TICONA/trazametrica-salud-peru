# Seguridad y endurecimiento

## Controles verificados

| Área | Control P17 |
|---|---|
| Contraseñas | Argon2id preferido; PBKDF2, PBKDF2-SHA1 y Scrypt quedan solo para verificación/migración |
| Sesiones | `HttpOnly`, `SameSite=Lax`, expiración al cerrar navegador y cookies `Secure` en demo |
| Transporte | redirección HTTPS, HSTS anual con subdominios y preload, hosts y orígenes CSRF explícitos |
| Navegador | CSP sin CSS/JS en línea, `frame-ancestors 'none'`, política de permisos y `nosniff` |
| Caché | respuestas autenticadas `private, no-store` y variación por cookie |
| Trazabilidad | UUID de correlación por solicitud y evento append-only ante capacidad denegada |
| Entrada | CSRF, límites XLSX, rechazo de macros/fórmulas/vínculos y columnas clínicas evidentes |
| Repositorio | escaneo de secretos conocidos, claves, bases, respaldos, binarios y correos no sintéticos |
| Dependencias | versiones fijadas, `pip-audit`, Bandit y contenedor sin usuario root |
| Despliegue | `manage.py check --deploy` con configuración demo externa y sintética |

La bitácora de denegación solo conserva método y ruta. No registra query string, cuerpo, cabeceras, token, contraseña ni contenido cargado.

## Criterio de bloqueo

Una credencial real, dato personal/clínico, vulnerabilidad alta o crítica sin excepción documentada, exención CSRF, `eval`/`exec`, configuración demo insegura o prueba negativa fallida bloquea G17.

## Riesgo residual

El estado conforme de P17 es evidencia interna del prototipo, no pentest, certificación OWASP, autorización sanitaria ni garantía productiva. El análisis antimalware real, el volumen privado, TLS/proxy del proveedor y la respuesta operativa a incidentes deben validarse nuevamente en P18.
