# Manual de operación

## 1. Preparación segura

1. Copie `.env.demo.example` como `.env.demo`; nunca publique ese archivo.
2. Genere valores aleatorios distintos para `DJANGO_SECRET_KEY`, `DATABASE_PASSWORD` y `BOOTSTRAP_ADMIN_PASSWORD`.
3. Conserve `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`, el origen CSRF local y `DEMO_CADDY_ADDRESS=:80`.
4. No abra el puerto `8080` en el router ni use túneles públicos. PostgreSQL permanece sin puertos publicados.

Las tres variables de seguridad con valor `false` en `.env.demo.example` permiten iniciar sesión exclusivamente por HTTP local. No son una configuración válida para Internet; los valores seguros predeterminados del código siguen siendo `true`.

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

Verifique `curl --fail http://localhost:8080/health/live/` y `curl --fail http://localhost:8080/health/ready/`, y abra `http://localhost:8080`. El usuario `admin_demo` es técnico, no una cuenta de atención clínica; la contraseña no aparece en ninguna salida.

## 3. Operación y detención

```bash
docker compose --env-file .env.demo -f compose.demo.yaml ps
docker compose --env-file .env.demo -f compose.demo.yaml logs --tail=200 web proxy
docker compose --env-file .env.demo -f compose.demo.yaml down
```

No use `down -v` en un entorno cuya evidencia deba conservarse: elimina volúmenes. Para reiniciar una demo desechable, documente primero el respaldo y la versión de semilla.

## 4. Respuesta inicial

Ante exposición de un secreto, dato real o comportamiento anómalo: detenga el stack, rote secretos, preserve los logs mínimos, evalúe alcance y registre la corrección. No convierta Git en un mecanismo de borrado de secretos.
