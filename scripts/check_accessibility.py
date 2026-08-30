from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "src" / "templates"

TH_WITHOUT_SCOPE = re.compile(r"<th\b(?![^>]*\bscope=)[^>]*>", re.IGNORECASE)
CONTROL = re.compile(r"<(input|select|textarea)\b([^>]*)>", re.IGNORECASE)
LABELLED_CONTROL = re.compile(r"\b(aria-label|aria-labelledby)=", re.IGNORECASE)
POSITIVE_TABINDEX = re.compile(r"\btabindex=[\"'](?:[1-9]\d*)[\"']", re.IGNORECASE)


def audit_templates() -> list[str]:
    errors: list[str] = []
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    required_base_fragments = (
        '<html lang="es">',
        '<meta name="viewport"',
        '<a class="skip-link" href="#main-content">',
        '<main id="main-content" tabindex="-1">',
    )
    for fragment in required_base_fragments:
        if fragment not in base:
            errors.append(f"base.html: falta {fragment}")

    for path in sorted(TEMPLATES.rglob("*.html")):
        relative = path.relative_to(ROOT)
        source = path.read_text(encoding="utf-8")
        if path.name != "base.html" and "{% block content %}" in source and "<h1" not in source:
            errors.append(f"{relative}: el flujo no declara h1")
        if "<style" in source or "<script" in source:
            errors.append(f"{relative}: contiene CSS o script en línea incompatible con CSP")
        if TH_WITHOUT_SCOPE.search(source):
            errors.append(f"{relative}: contiene encabezados de tabla sin scope")
        if POSITIVE_TABINDEX.search(source):
            errors.append(f"{relative}: contiene tabindex positivo")

        for match in CONTROL.finditer(source):
            tag, attributes = match.groups()
            if tag.casefold() == "input" and re.search(
                r"\btype=[\"']hidden[\"']", attributes, re.IGNORECASE
            ):
                continue
            before = source[max(0, match.start() - 160) : match.start()]
            wrapped = before.rfind("<label") > before.rfind("</label>")
            if not wrapped and not LABELLED_CONTROL.search(attributes):
                errors.append(f"{relative}: control {tag} sin etiqueta accesible")
    return errors


def main() -> int:
    errors = audit_templates()
    if errors:
        for error in errors:
            print(error)
        return 1
    count = len(list(TEMPLATES.rglob("*.html")))
    print(f"Accesibilidad estructural conforme: {count} plantillas verificadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
