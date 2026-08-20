# Seguridad y límites de confianza

## 1. Activos y fronteras

Activos principales: cuentas, permisos, datos sintéticos, fórmulas, decisiones de aprobación, evidencias, exportaciones, bitácora, secretos y artefactos de construcción.

Fronteras: navegador–web, web–PostgreSQL, worker–PostgreSQL, aplicación–archivos y aplicación–exportaciones. Aunque los datos sean sintéticos, el sistema debe demostrar controles aplicables a un producto administrativo serio.

## 2. Controles obligatorios

| ID | Control arquitectónico |
|---|---|
| SEG-01 | Usuario Django personalizado desde la primera migración |
| SEG-02 | Sesiones de servidor, cookies `HttpOnly`, `Secure` en demo y política `SameSite` explícita |
| SEG-03 | Protección CSRF en toda mutación y prohibición de desactivarla globalmente |
| SEG-04 | Permisos en servicios y vistas; ocultar interfaz no reemplaza autorización |
| SEG-05 | Argon2 como hasher preferido y validadores de contraseña activos |
| SEG-06 | Separación autor–aprobador y auditor–cerrador |
| SEG-07 | `DEBUG=False`, hosts explícitos, HTTPS y cabeceras seguras en demo |
| SEG-08 | Secretos externos, rotables y ausentes del repositorio/logs |
| SEG-09 | Cargas en cuarentena lógica antes de promoción |
| SEG-10 | Tamaño, extensión, contenido, plantilla, nombre seguro y hash validados |
| SEG-11 | Evidencias privadas descargadas mediante vista autorizada |
| SEG-12 | Fórmulas mediante operadores y funciones permitidas; prohibido `eval`/`exec` |
| SEG-13 | Consultas ORM parametrizadas; SQL manual excepcional y revisado |
| SEG-14 | Escape de salida por defecto y sanitización explícita de contenido enriquecido |
| SEG-15 | Bitácora append-only para la aplicación ordinaria y eventos correlacionados |
| SEG-16 | Logs estructurados sin credenciales, tokens, archivos ni contenido cargado |
| SEG-17 | Exportaciones con permiso, filtros, versión y marca `DATOS SINTÉTICOS` |

## 3. Amenazas prioritarias

| Amenaza | Escenario | Mitigación |
|---|---|---|
| Suplantación | Credencial reutilizada o sesión robada | Hash fuerte, cookies seguras, rotación y cierre de sesión |
| Elevación | Usuario invoca URL no visible | Autorización en servidor y pruebas negativas |
| Manipulación | Cambio directo de versión aprobada | Inmutabilidad funcional y nuevas versiones |
| Repudio | Actor niega aprobación/exportación | Bitácora con actor, instante, objeto y resultado |
| Divulgación | Error o log expone configuración | Filtros, `DEBUG=False` y logs mínimos |
| Denegación | Archivo excesivo o carga repetida | Límites, hash, tiempos y estados persistentes |
| Código malicioso | Fórmula o archivo intenta ejecutar contenido | Motor de fórmula restringido; no macros ni evaluación dinámica |
| Datos reales | Usuario carga información identificable | Validador preventivo, rechazo y política sintética |

## 4. Archivos y fórmulas

- El MVP aceptará `.xlsx` sin macros y `.csv` cuando el caso lo requiera; `.xlsm`, ejecutables y archivos comprimidos quedan bloqueados.
- La extensión no será prueba suficiente: se validará estructura y contenido esperado.
- Nombres originales solo serán metadatos; la ruta física será generada.
- Las fórmulas KPI se almacenarán como estructura declarativa o expresión analizada con lista permitida.
- No se importarán fórmulas Excel como código ejecutable ni se confiará en resultados precalculados sin validación.

## 5. Despliegue seguro

Antes de demo pública deben aprobarse `check --deploy`, TLS, hosts, proxy, cookies, CSRF, cabeceras, permisos de archivos, cuenta PostgreSQL restringida, copia/restauración y escaneo de dependencias. La [lista de despliegue de Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) será evidencia, no sustituto de las pruebas de P17.

## 6. Incidentes

La respuesta mínima será contener, revocar, preservar evidencia técnica limitada, determinar alcance, corregir, probar y registrar. Si aparece un dato o secreto real, la prioridad será detener su exposición; eliminar el archivo visible no garantiza eliminarlo del historial Git.
