from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.accounts.models import User
from apps.analytics.demo_seed import seed_analytics


class Command(BaseCommand):
    help = "Crea definiciones y ejecuciones estadísticas exclusivamente sintéticas."

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
            result = seed_analytics(actor=actor, dataset_version=str(options["dataset_version"]))
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                "Semilla P16 conforme: "
                f"{result['definitions']} definiciones, {result['runs']} ejecuciones y "
                f"{result['quality_passed']} puertas de calidad superadas."
            )
        )
