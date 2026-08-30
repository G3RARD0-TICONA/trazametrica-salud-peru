# Recuperación operativa

## Respaldo antes de intervenir

```bash
docker compose --env-file .env.demo -f compose.demo.yaml exec -T db \
  pg_dump --format=custom --no-owner --username="$DATABASE_USER" "$DATABASE_NAME" > demo.dump
docker compose --env-file .env.demo -f compose.demo.yaml exec web \
  python src/manage.py recovery_manifest > recovery-manifest-before.json
```

Custodie `demo.dump` y el manifiesto fuera del servidor, cifrados y con acceso limitado. Contienen únicamente datos sintéticos en esta demo, pero no deben publicarse en el repositorio.

## Restauración aislada

1. Cree una base de restauración separada; nunca aplique `--clean` contra una base no verificada.
2. Restaure el volcado en esa base con `pg_restore --clean --if-exists --no-owner`.
3. Ejecute `python src/manage.py migrate --noinput` y `python src/manage.py recovery_manifest --compare recovery-manifest-before.json` contra la base aislada.
4. Verifique `/health/ready/`, roles y conteos sintéticos antes de cambiar tráfico.
5. Documente fecha, operador, hashes y resultado; solo entonces autorice el intercambio controlado.

## Retención demostrativa

Conserve como mínimo el último respaldo verificado y el manifiesto asociado. Defina periodo, ubicación, cifrado y responsables antes de habilitar un proveedor público. El repositorio no almacena respaldos, claves ni datos de la demo.
