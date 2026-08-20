# Política de seguridad y datos

## Alcance actual

Trazamétrica Salud Perú es un proyecto demostrativo en construcción. No está autorizado para operar con pacientes, historias clínicas ni sistemas de producción.

## Regla de datos sintéticos

Solo se permiten datos ficticios generados para pruebas. Antes de confirmar cualquier cambio se debe comprobar que no contenga:

- nombres, DNI, pasaporte u otro identificador real;
- teléfono, dirección, correo personal o geolocalización individual;
- diagnóstico, tratamiento, resultado, receta o historia clínica;
- información laboral, financiera o biométrica identificable;
- credenciales, tokens, claves privadas, cadenas de conexión o archivos `.env`;
- respaldos, exportaciones, registros o capturas de sistemas reales.

Los datos sintéticos deberán estar señalados como tales, tener una versión y poder regenerarse sin una fuente real.

## Controles mínimos del desarrollo

- Separar configuración y secretos del código.
- Mantener permisos de mínimo privilegio.
- Registrar cambios críticos en una bitácora inmutable para el usuario ordinario.
- Validar tipo, estructura, tamaño y contenido de archivos importados.
- Evitar que mensajes de error expongan datos o configuración sensible.
- Revisar dependencias y ejecutar pruebas antes de integrar cambios.
- Marcar exportaciones y tableros de demostración como `DATOS SINTÉTICOS`.

## Reporte de vulnerabilidades

No publiques detalles sensibles, credenciales ni pruebas con datos reales en una incidencia. Las observaciones no sensibles pueden registrarse mediante GitHub Issues. Para una vulnerabilidad explotable, utiliza el canal privado de seguridad de GitHub si se encuentra habilitado; si no lo está, solicita primero un canal privado sin revelar el detalle técnico.

## Respuesta inicial

Ante una exposición accidental se deberá detener la publicación, revocar las credenciales afectadas, preservar evidencia mínima, evaluar el alcance y documentar la corrección. El historial Git no debe considerarse un mecanismo de eliminación segura de secretos.
