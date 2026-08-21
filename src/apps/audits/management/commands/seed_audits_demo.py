from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.accounts.models import User
from apps.audits.demo_seed import seed_audits


class Command(BaseCommand):
    help = "Crea 12 planes, 180 respuestas y 180 hallazgos exclusivamente sintéticos."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--actor", required=True)
        parser.add_argument("--dataset-version", default="1")

    def handle(self, *args: object, **options: object) -> None:
        if settings.ENVIRONMENT not in {"local", "test", "demo"}:
            raise CommandError("La semilla solo está permitida en local, test o demo.")
        try:
            actor = User.objects.get(username=options["actor"], is_active=True)
        except User.DoesNotExist as exc:
            raise CommandError("El actor activo no existe.") from exc
        try:
            result = seed_audits(
                actor=actor,
                dataset_version=str(options["dataset_version"]),
            )
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                "Semilla P12 conforme: "
                f"{result['plans']} planes, {result['checklists']} listas, "
                f"{result['executions']} ejecuciones, {result['responses']} respuestas, "
                f"{result['findings']} hallazgos y {result['evidence']} evidencias sintéticas."
            )
        )
