from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.accounts.models import User
from apps.reports.demo_seed import seed_reports


class Command(BaseCommand):
    help = "Crea contratos publicados para reportes exclusivamente sintéticos."

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
            result = seed_reports(actor=actor, dataset_version=str(options["dataset_version"]))
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        self.stdout.write(
            self.style.SUCCESS(f"Semilla P15 conforme: {result['contracts']} contratos publicados.")
        )
