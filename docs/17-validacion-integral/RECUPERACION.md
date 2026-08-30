# Recuperación e integridad

## Contrato

El comando `recovery_manifest` genera un JSON con:

- proveedor de base de datos;
- migraciones aplicadas;
- conteos de todos los modelos administrados;
- hash del manifiesto de archivos sintéticos;
- huella SHA-256 del contenido estable.

## Simulacro aislado

```bash
python src/manage.py recovery_manifest > before.json
pg_dump --format=custom --file=demo.dump "$DATABASE_URL"

# Restaurar únicamente en una base vacía y aislada.
pg_restore --clean --if-exists --no-owner --dbname="$RESTORE_DATABASE_URL" demo.dump
DATABASE_URL="$RESTORE_DATABASE_URL" python src/manage.py migrate --noinput
DATABASE_URL="$RESTORE_DATABASE_URL" python src/manage.py recovery_manifest --compare before.json
```

La restauración es conforme solo si la comparación termina correctamente y las pruebas de vida, preparación y autenticación responden. Nunca se debe ejecutar `--clean` contra una base no verificada o productiva.

P17 valida el contrato y su detección de divergencias. P18 ejecutará el simulacro sobre el proveedor elegido, incorporará el almacenamiento privado definitivo y fijará retención, cifrado, custodia y recuperación operativa.
