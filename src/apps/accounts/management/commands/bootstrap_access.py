import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.policies import ROLE_CAPABILITIES
from apps.accounts.services import assign_role

ROLE_NAMES = {
    "ADMIN_SYSTEM": "Administrador del sistema",
    "QUALITY_MANAGER": "Responsable de calidad",
    "PROCESS_OWNER": "Responsable de proceso",
    "INDICATOR_ANALYST": "Analista de indicadores",
    "DATA_LOADER": "Cargador de datos",
    "AUDITOR": "Auditor",
    "APPROVER": "Aprobador",
    "VIEWER": "Consulta",
}


class Command(BaseCommand):
    help = "Crea la cuenta técnica inicial y los ocho roles del entorno sintético."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--username", default="admin_demo")

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        if settings.ENVIRONMENT not in {"local", "test", "demo"}:
            raise CommandError("El bootstrap solo está permitido en local, test o demo.")

        password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
        if not password or len(password) < 12:
            raise CommandError(
                "Defina BOOTSTRAP_ADMIN_PASSWORD con al menos 12 caracteres; no se imprime."
            )

        username = str(options["username"])
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "bootstrap_reason": "Bootstrap autorizado del entorno sintético.",
            },
        )
        if created:
            user.set_password(password)
            user.full_clean()
            user.save()
        elif not user.is_superuser:
            raise CommandError("El usuario existente no es una cuenta técnica inicial.")

        for code, capabilities in ROLE_CAPABILITIES.items():
            role, role_created = Role.objects.get_or_create(
                code=code,
                defaults={
                    "name": ROLE_NAMES[code],
                    "description": f"Rol sintético con {len(capabilities)} capacidades.",
                    "is_approval_role": code == "APPROVER",
                    "created_by": user,
                    "updated_by": user,
                },
            )
            if not role_created:
                role.name = ROLE_NAMES[code]
                role.description = f"Rol sintético con {len(capabilities)} capacidades."
                role.is_approval_role = code == "APPROVER"
                role.updated_by = user
                role.save(
                    update_fields=["name", "description", "is_approval_role", "updated_by"]
                )

        admin_role = Role.objects.get(code="ADMIN_SYSTEM")
        if not user.role_assignments.filter(role=admin_role, valid_to__isnull=True).exists():
            assign_role(
                actor=user,
                user=user,
                role=admin_role,
                valid_from=timezone.localdate(),
            )

        action = "creada" if created else "verificada"
        self.stdout.write(self.style.SUCCESS(f"Cuenta {username} {action}; 8 roles conformes."))
