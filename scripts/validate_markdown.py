from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
IGNORED_PARTS = {".git", ".venv", "node_modules"}


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        errors.append(f"{path.relative_to(ROOT)}: falta salto de línea final")

    for target in LINK_PATTERN.findall(text):
        clean_target = target.split("#", maxsplit=1)[0].strip()
        if not clean_target or "://" in clean_target or clean_target.startswith("mailto:"):
            continue
        resolved = (path.parent / clean_target).resolve()
        if not resolved.exists():
            errors.append(
                f"{path.relative_to(ROOT)}: enlace local inexistente: {clean_target}"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.md")):
        if any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
            continue
        errors.extend(validate_file(path))
    if errors:
        print("\n".join(errors))
        return 1
    print("Documentación Markdown válida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
