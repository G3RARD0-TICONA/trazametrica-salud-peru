# Publicación final

## Condiciones antes de crear una release

- CI del PR P18 aprobada y expediente G18 actualizado.
- Simulacro realizado sobre el proveedor, DNS y TLS controlados por el titular.
- `/health/live/` y `/health/ready/` conformes a través del proxy.
- aviso de datos sintéticos/no clínico visible desde el navegador público.
- secreto, contraseña y respaldo fuera del repositorio; PostgreSQL no expuesto.
- propietario valida manuales, recuperación y la URL publicada.

## Procedimiento de release

1. Integre el PR P18 autorizado mediante squash.
2. Cree el tag anotado `v0.1.0` sobre el commit de `main` integrado.
3. Publique una GitHub Release con el resumen de P00–P18, enlace al commit, evidencia CI y estos límites: demo sintética, administrativa y no clínica.
4. Añada la URL pública solo después de la verificación del titular; nunca agregue credenciales ni datos de operación.
5. Registre fecha, versión, hash de imagen y responsable de publicación en el expediente G18.

La release pública muestra código y documentación; no acredita certificación, afiliación, autorización sanitaria, seguridad productiva ni uso institucional.
