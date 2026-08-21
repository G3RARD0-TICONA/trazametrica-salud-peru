# Ejecución local y demostrativa

## 1. Requisitos

- Docker Engine con Docker Compose Specification.
- Puertos locales 8000 y 5432 disponibles.
- Ningún dato o secreto real.

## 2. Preparación

1. Copiar `.env.example` a `.env`.
2. Sustituir las claves de ejemplo por valores locales no reutilizados.
3. No confirmar `.env` en Git; el `.gitignore` del repositorio lo excluye.

## 3. Inicio

```bash
docker compose up --build -d
docker compose exec web python src/manage.py migrate --noinput
docker compose exec web python src/manage.py bootstrap_access
```

El tercer comando requiere que `.env` defina `BOOTSTRAP_ADMIN_PASSWORD` con al menos 12 caracteres. La salida confirma la cuenta, pero nunca revela la contraseña.

## 4. Verificación

```bash
curl --fail http://localhost:8000/health/live/
curl --fail http://localhost:8000/health/ready/
docker compose exec web python src/manage.py check
docker compose exec web pytest
```

- `/health/live/` confirma que el proceso web responde.
- `/health/ready/` confirma también la conexión PostgreSQL.
- La portada redirige a `/accounts/login/`.
- Una cuenta sin rol vigente recibe HTTP 403 después de autenticarse.

## 5. Detención

```bash
docker compose down
```

Para conservar evidencia reproducible, no se incluye una instrucción automática que elimine volúmenes. Si el entorno sintético debe reiniciarse, la eliminación de datos debe ser una decisión explícita del responsable.

## 6. Entornos

| Entorno | Configuración | Datos permitidos |
|---|---|---|
| Local | `config.settings.local` | Sintéticos |
| Pruebas | `config.settings.test` | Sintéticos, efímeros |
| Demo | `config.settings.demo` | Sintéticos y públicos |

La configuración `demo` exige `DJANGO_SECRET_KEY`, activa cookies seguras y presupone terminación TLS. Este procedimiento no autoriza un despliegue clínico real.
