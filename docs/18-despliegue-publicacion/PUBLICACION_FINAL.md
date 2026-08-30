# Publicación final

## Condiciones antes de crear una release

- CI del PR P18 aprobada y expediente G18 actualizado.
- Simulacro local completo realizado por Docker Compose en CI.
- `/health/live/` y `/health/ready/` conformes a través del proxy.
- aviso de datos sintéticos/no clínico visible desde el navegador local.
- secreto, contraseña y respaldo fuera del repositorio; PostgreSQL no expuesto.
- propietario valida manuales, recuperación y alcance sin hosting público.

## Procedimiento de release

1. Integre el PR P18 autorizado mediante squash.
2. Cree el tag anotado `v0.1.0` sobre el commit de `main` integrado.
3. Publique una GitHub Release con el resumen de P00–P18, enlace al commit, evidencia CI y estos límites: demo sintética, administrativa y no clínica.
4. Adjunte las instrucciones para ejecutar la demo local; no anuncie una URL de aplicación ni agregue credenciales o datos de operación.
5. Registre fecha, versión, commit y responsable de publicación en el expediente G18.

La release pública muestra código y documentación; GitHub no ejecuta el servicio Django. La publicación no acredita certificación, afiliación, autorización sanitaria, seguridad productiva ni uso institucional.
