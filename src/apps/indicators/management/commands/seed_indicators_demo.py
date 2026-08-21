from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.accounts.models import User
from apps.indicators.demo_seed import seed_indicators


class Command(BaseCommand):
    help = "Crea 200 KPI, 260 versiones y observaciones exclusivamente sintéticas."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--actor", required=True)
        parser.add_argument("--dataset-version", default="1")
        parser.add_argument("--observation-count", type=int, default=100_000)

    def handle(self, *args: object, **options: object) -> None:
        if settings.ENVIRONMENT not in {"local", "test", "demo"}:
            raise CommandError("La semilla solo está permitida en local, test o demo.")
        try:
            actor = User.objects.get(username=options["actor"], is_active=True)
        except User.DoesNotExist as exc:
            raise CommandError("El actor activo no existe.") from exc
        try:
            result = seed_indicators(
                actor=actor,
                dataset_version=str(options["dataset_version"]),
                observation_count=int(str(options["observation_count"])),
            )
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                "Semilla P11 conforme: "
                f"{result['indicators']} KPI, {result['versions']} versiones y "
                f"{result['observations']} observaciones sintéticas."
            )
        )
