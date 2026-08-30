# Manual de operación

## 1. Preparación segura

1. Copie `.env.demo.example` como `.env.demo`; nunca publique ese archivo.
2. Genere valores aleatorios distintos para `DJANGO_SECRET_KEY`, `DATABASE_PASSWORD` y `BOOTSTRAP_ADMIN_PASSWORD`.
3. Defina `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` y `DEMO_CADDY_ADDRESS` con el dominio propio antes de exponer Internet.
4. Mantenga PostgreSQL sin puertos publicados y permita en el firewall únicamente 80/443 hacia Caddy.

## 2. Arranque demostrativo

```bash
cp .env.demo.example .env.demo
docker compose --env-file .env.demo -f compose.demo.yaml up --build -d
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py bootstrap_access
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_organizations_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_processes_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_import_templates_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_indicators_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_audits_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_improvements_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_risks_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_reports_demo --actor admin_demo
docker compose --env-file .env.demo -f compose.demo.yaml exec web python src/manage.py seed_analytics_demo --actor admin_demo
```

Verifique `curl --fail http://localhost:8080/health/live/` y `curl --fail http://localhost:8080/health/ready/`. El usuario `admin_demo` es técnico, no una cuenta de atención clínica; la contraseña no aparece en ninguna salida.

## 3. Operación y detención

```bash
docker compose --env-file .env.demo -f compose.demo.yaml ps
docker compose --env-file .env.demo -f compose.demo.yaml logs --tail=200 web proxy
docker compose --env-file .env.demo -f compose.demo.yaml down
```

No use `down -v` en un entorno cuya evidencia deba conservarse: elimina volúmenes. Para reiniciar una demo desechable, documente primero el respaldo y la versión de semilla.

## 4. Respuesta inicial

Ante exposición de un secreto, dato real o comportamiento anómalo: retire el acceso público, rote secretos, preserve los logs mínimos, evalúe alcance y registre la corrección. No convierta Git en un mecanismo de borrado de secretos.
