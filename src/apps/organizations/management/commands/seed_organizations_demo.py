from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.accounts.models import User
from apps.organizations.demo_seed import seed_organization_catalog


class Command(BaseCommand):
    help = "Genera el catálogo organizacional sintético y determinista de P07."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--actor", default="admin_demo")
        parser.add_argument("--dataset-version", choices=["1"], default="1")

    def handle(self, *args: object, **options: object) -> None:
        if settings.ENVIRONMENT not in {"local", "test", "demo"}:
            raise CommandError("La semilla solo está permitida en local, test o demo.")
        actor = User.objects.filter(
            username=str(options["actor"]),
            is_active=True,
        ).first()
        if actor is None:
            raise CommandError(
                "No existe el actor activo indicado; ejecute primero bootstrap_access."
            )
        counts = seed_organization_catalog(actor=actor)
        self.stdout.write(
            self.style.SUCCESS(
                "Catálogo P07 conforme: "
                f"{counts['organizations']} organización, {counts['sites']} sedes, "
                f"{counts['services']} servicios y {counts['areas']} áreas."
            )
        )
