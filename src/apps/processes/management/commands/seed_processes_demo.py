from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.accounts.models import User
from apps.processes.demo_seed import seed_processes


class Command(BaseCommand):
    help = "Crea 100 procesos y fichas SIPOC exclusivamente sintéticos."

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
        result = seed_processes(
            actor=actor,
            dataset_version=str(options["dataset_version"]),
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Semilla P09 conforme: "
                f"{result['processes']} procesos, {result['versions']} versiones y "
                f"{result['entries']} entradas SIPOC."
            )
        )
