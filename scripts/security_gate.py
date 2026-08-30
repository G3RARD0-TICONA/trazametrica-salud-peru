from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ENV_EXAMPLE = ".env.example"
FORBIDDEN_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".sqlite3", ".dump", ".bak"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "OpenAI key": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
}
REAL_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.IGNORECASE)
RESERVED_EMAIL_DOMAINS = {"example.com", "example.net", "example.org"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def python_calls_forbidden(source: str) -> bool:
    tree = ast.parse(source)
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"eval", "exec"}
        for node in ast.walk(tree)
    )


def audit_repository() -> list[str]:
    errors: list[str] = []
    for path in tracked_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative != ALLOWED_ENV_EXAMPLE and (
            path.name == ".env" or path.suffix.casefold() in FORBIDDEN_SUFFIXES
        ):
            errors.append(f"archivo prohibido: {relative}")
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            errors.append(f"archivo rastreado mayor a 5 MiB: {relative}")
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"binario rastreado no aprobado: {relative}")
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(source):
                errors.append(f"posible {label}: {relative}")
        if relative.startswith(("src/", "tests/", "data/")):
            for match in REAL_EMAIL.finditer(source):
                domain = match.group(1).casefold()
                if not domain.endswith(".invalid") and domain not in RESERVED_EMAIL_DOMAINS:
                    errors.append(f"correo no sintético: {relative}")
                    break
        if relative.startswith("src/") and "@csrf_exempt" in source:
            errors.append(f"exención CSRF no permitida: {relative}")
        if path.suffix == ".py" and relative.startswith("src/"):
            try:
                if python_calls_forbidden(source):
                    errors.append(f"eval/exec no permitido: {relative}")
            except SyntaxError as exc:
                errors.append(f"Python inválido en {relative}: {exc}")
    return errors


def main() -> int:
    errors = audit_repository()
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Puerta de repositorio segura: sin secretos, datos reales ni artefactos prohibidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
