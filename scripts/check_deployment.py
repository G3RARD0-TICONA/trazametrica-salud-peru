from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *fragments: str) -> list[str]:
    content = (ROOT / path).read_text(encoding="utf-8")
    return [f"{path}: falta {fragment!r}" for fragment in fragments if fragment not in content]


def main() -> int:
    failures: list[str] = []
    failures.extend(
        require(
            "Dockerfile",
            'CMD ["gunicorn", "config.wsgi:application"',
            'ENTRYPOINT ["/app/deploy/entrypoint.sh"]',
            "HEALTHCHECK",
        )
    )
    failures.extend(
        require(
            "deploy/entrypoint.sh",
            "manage.py check --deploy",
            "manage.py migrate --noinput",
            "manage.py collectstatic --noinput",
        )
    )
    failures.extend(
        require(
            "compose.demo.yaml",
            "postgres:17.11-alpine",
            "private_demo_data",
            "static_demo_data",
            "caddy:2.10.2-alpine",
        )
    )
    failures.extend(
        require(
            "deploy/Caddyfile",
            "reverse_proxy web:8000",
            "health_uri /health/live/",
            "handle_path /static/*",
            "X-Content-Type-Options",
        )
    )
    failures.extend(
        require(
            "docs/18-despliegue-publicacion/README.md",
            "DATOS SINTÉTICOS",
            "no clínica",
            "aceptación formal",
        )
    )
    failures.extend(
        require(
            ".github/workflows/ci.yml",
            "compose.demo.yaml up --build --detach",
            "http://127.0.0.1:8080/health/ready/",
            "compose.demo.yaml down --volumes",
        )
    )
    if failures:
        print("\n".join(failures))
        return 1
    print("Contrato de despliegue demostrativo conforme.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
