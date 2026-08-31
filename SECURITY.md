# Política de seguridad

Trazamétrica Salud Perú es una demostración administrativa, no clínica, construida exclusivamente con datos sintéticos. Esta política explica cómo reportar vulnerabilidades, qué controles protegen el proyecto y cuáles son sus límites operativos.

## Versiones cubiertas

La revisión de seguridad se concentra en la última versión pública y en la rama `main`.

| Versión | Estado |
|---|---|
| `v0.1.x` | versión pública vigente |
| `main` | siguiente estado integrado |
| ramas y commits anteriores | sin mantenimiento independiente |

El proyecto no ofrece un SLA de soporte o corrección. Los reportes se priorizan según impacto, reproducibilidad y riesgo para los usuarios del repositorio.

## Reportar una vulnerabilidad

No publique una vulnerabilidad explotable, un secreto ni una prueba sensible en GitHub Issues, discusiones, pull requests o comentarios.

1. Abra la pestaña **Security** del repositorio.
2. Use **Report a vulnerability** si el reporte privado de GitHub está habilitado.
3. Si esa opción no aparece, abra una incidencia pública que solicite únicamente un canal privado, sin revelar el detalle técnico.

Incluya en el reporte privado:

- versión, commit o entorno afectado;
- componente y tipo de vulnerabilidad;
- impacto observado y escenario de abuso;
- pasos mínimos para reproducirla con datos ficticios;
- evidencia sanitizada, sin tokens, contraseñas ni información real;
- mitigación sugerida, si dispone de una.

No ejecute pruebas contra sistemas de terceros, clínicas, personas ni infraestructura que no controle. No utilice datos personales o clínicos para demostrar el hallazgo.

## Política estricta de datos sintéticos

El repositorio, los reportes y la demo solo admiten información ficticia y regenerable. Está prohibido incorporar:

- nombres, DNI, pasaportes u otros identificadores reales;
- teléfonos, direcciones, correos personales o geolocalización individual;
- diagnósticos, tratamientos, recetas, resultados o historias clínicas;
- datos laborales, financieros o biométricos identificables;
- credenciales, tokens, claves privadas, cadenas de conexión o archivos `.env`;
- respaldos, exportaciones, logs, capturas o documentos de sistemas reales.

Las cargas Excel deben conservar la marca `DATOS SINTÉTICOS`. El sistema rechaza macros, fórmulas, vínculos externos, objetos incrustados, columnas clínicas evidentes y correos que no utilicen dominios reservados o `.invalid`.

## Controles implementados

| Área | Controles demostrativos |
|---|---|
| Identidad | Argon2id preferido, roles por capacidad, vigencias, mínimo privilegio y desactivación controlada |
| Segregación | autores, revisores y aprobadores separados en operaciones críticas |
| Sesión y navegador | CSRF, cookies endurecidas por defecto, CSP, `nosniff`, protección de marcos y caché privada |
| Entradas y archivos | límites estructurales, validación OOXML, rechazo de macros/fórmulas/vínculos y confirmación sintética |
| Trazabilidad | UUID de correlación, hashes SHA-256 y eventos append-only sin cuerpo ni query string |
| Exportaciones | neutralización de fórmulas y marca visible de datos sintéticos en CSV, XLSX y PDF |
| Repositorio | bloqueo de secretos conocidos, datos reales, binarios, respaldos y artefactos mayores a 5 MiB |
| Dependencias y código | versiones fijadas, Ruff, mypy, Bandit, `pip-audit`, pruebas y cobertura mínima de 80 % |
| Contenedores | proceso web no privilegiado, PostgreSQL sin puerto público y comprobaciones de salud |

La bitácora de solicitudes denegadas registra únicamente método, ruta y correlación. No conserva query strings, cuerpos, cabeceras, tokens, contraseñas ni contenido cargado.

## Perfiles de ejecución

### Pruebas

La CI utiliza Python 3.13 y PostgreSQL 17 con secretos sintéticos efímeros. Cada cambio valida documentación, lint, tipos, migraciones, seguridad del repositorio, pruebas, cobertura, Bandit, dependencias y el stack Docker.

### Demostración local

La configuración `.env.demo.example` permite HTTP únicamente en `localhost`. Las opciones de redirección HTTPS y cookies `Secure` se desactivan expresamente para ese perfil local; sus valores seguros permanecen activados por defecto en el código.

No exponga el puerto `8080`, no configure túneles y no reenvíe puertos del router. PostgreSQL no publica un puerto. GitHub aloja el repositorio y la release, no la aplicación Django.

### Producción

No existe un perfil productivo aprobado. Un despliegue real requeriría, como mínimo, evaluación jurídica y de protección de datos, HTTPS, gestión externa de secretos, almacenamiento privado, análisis antimalware, respaldos cifrados, monitorización, respuesta a incidentes, revisión independiente de permisos y pruebas de penetración.

## Limitaciones conocidas

- Los resultados de CI son evidencia interna reproducible, no una certificación de seguridad.
- Bandit y `pip-audit` no sustituyen una revisión manual, SAST/DAST amplio ni pentest.
- La validación de archivos no incorpora un motor antimalware real.
- La demo local por HTTP no protege tráfico expuesto a otras redes y por eso debe permanecer en `localhost`.
- El control append-only se aplica en la capa de aplicación y no acredita inmutabilidad criptográfica externa.
- La revisión de accesibilidad no equivale a una certificación WCAG.
- El proyecto no está autorizado para procesar datos personales, clínicos o confidenciales reales.

## Respuesta inicial ante incidentes

Ante la exposición accidental de un secreto, dato real o comportamiento anómalo:

1. detenga la demo o retire el artefacto expuesto;
2. revoque y rote inmediatamente las credenciales afectadas;
3. preserve evidencia mínima sin copiar información sensible a Issues o Git;
4. determine versiones, componentes y alcance;
5. corrija y agregue una prueba de regresión con datos sintéticos;
6. documente la decisión y publique un aviso cuando corresponda.

Reescribir o eliminar un commit no garantiza que un secreto haya desaparecido de clones, cachés o forks. La rotación de la credencial es obligatoria.

## Divulgación responsable

Permita verificar y corregir el hallazgo antes de divulgar detalles explotables. No se promete una fecha fija de respuesta, pero se procurará mantener comunicación sobre validación, severidad y corrección. La eventual publicación debe omitir credenciales, datos reales y procedimientos que expongan a terceros.

## Alcance institucional y legal

Esta política no constituye certificación OWASP, autorización sanitaria, garantía de seguridad productiva ni afiliación con MINSA, SUSALUD, ISO, JCI, una clínica o un proveedor tecnológico. El proyecto sigue siendo una demostración independiente y no clínica.

Los derechos y condiciones de reutilización se encuentran en [NOTICE.md](NOTICE.md).
