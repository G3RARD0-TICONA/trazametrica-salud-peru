from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.core.recovery import manifest_matches, recovery_manifest


class Command(BaseCommand):
    help = "Genera o compara el manifiesto de integridad para un simulacro de restauración."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--compare",
            type=Path,
            help="Archivo JSON generado antes del respaldo que debe coincidir.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        observed = recovery_manifest()
        compare_path = options.get("compare")
        if compare_path is not None:
            try:
                expected = json.loads(compare_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CommandError("No se pudo leer el manifiesto esperado.") from exc
            if not manifest_matches(expected, observed):
                raise CommandError("La restauración no coincide con el manifiesto esperado.")
            self.stdout.write(self.style.SUCCESS("Manifiesto de restauración conforme."))
            return
        self.stdout.write(json.dumps(observed, ensure_ascii=False, indent=2, sort_keys=True))
