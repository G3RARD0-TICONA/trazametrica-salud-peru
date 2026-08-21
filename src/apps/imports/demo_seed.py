from __future__ import annotations

import uuid
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.organizations.models import Organization

from .models import (
    ImportTemplate,
    ImportTemplateVersion,
    TemplateTargetType,
    TemplateVersionStatus,
)
from .services import normalize_schema, schema_hash

DEMO_NAMESPACE = uuid.UUID("702827f4-83fb-5e92-a470-e163b64c5dc5")
DEMO_VALID_FROM = date(2026, 1, 1)


def demo_import_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


TEMPLATE_CATALOG: tuple[tuple[str, str, TemplateTargetType, list[dict[str, object]]], ...] = (
    (
        "IMP-KPI",
        "Observaciones KPI Sintéticas",
        TemplateTargetType.KPI_OBSERVATIONS,
        [
            {
                "name": "observation_code",
                "type": "string",
                "required": True,
                "max_length": 50,
                "pattern": "^[A-Z0-9-]+$",
                "unique_in_file": True,
            },
            {"name": "site_code", "type": "string", "required": True, "max_length": 50},
            {"name": "service_code", "type": "string", "required": True, "max_length": 50},
            {"name": "period_start", "type": "date", "required": True},
            {"name": "period_end", "type": "date", "required": True},
            {"name": "value", "type": "decimal", "required": True, "min": 0, "max": 1000000},
            {"name": "dimension_key", "type": "string", "required": True, "max_length": 200},
        ],
    ),
    (
        "IMP-AUD",
        "Hallazgos de Auditoría Sintéticos",
        TemplateTargetType.AUDIT_FINDINGS,
        [
            {
                "name": "finding_code",
                "type": "string",
                "required": True,
                "max_length": 50,
                "pattern": "^[A-Z0-9-]+$",
                "unique_in_file": True,
            },
            {"name": "process_code", "type": "string", "required": True, "max_length": 50},
            {"name": "criterion", "type": "string", "required": True, "max_length": 500},
            {"name": "condition", "type": "string", "required": True, "max_length": 500},
            {
                "name": "impact",
                "type": "string",
                "required": True,
                "choices": ["low", "medium", "high", "critical"],
            },
        ],
    ),
    (
        "IMP-CAP",
        "Acciones Correctivas Sintéticas",
        TemplateTargetType.CORRECTIVE_ACTIONS,
        [
            {
                "name": "action_code",
                "type": "string",
                "required": True,
                "max_length": 50,
                "pattern": "^[A-Z0-9-]+$",
                "unique_in_file": True,
            },
            {"name": "finding_code", "type": "string", "required": True, "max_length": 50},
            {"name": "description", "type": "string", "required": True, "max_length": 500},
            {"name": "owner_code", "type": "string", "required": True, "max_length": 50},
            {"name": "due_date", "type": "date", "required": True, "allow_future": True},
        ],
    ),
    (
        "IMP-RIE",
        "Riesgos Sintéticos",
        TemplateTargetType.RISKS,
        [
            {
                "name": "risk_code",
                "type": "string",
                "required": True,
                "max_length": 50,
                "pattern": "^[A-Z0-9-]+$",
                "unique_in_file": True,
            },
            {"name": "process_code", "type": "string", "required": True, "max_length": 50},
            {"name": "cause", "type": "string", "required": True, "max_length": 500},
            {"name": "event", "type": "string", "required": True, "max_length": 500},
            {"name": "consequence", "type": "string", "required": True, "max_length": 500},
            {"name": "probability", "type": "integer", "required": True, "min": 1, "max": 5},
            {"name": "impact", "type": "integer", "required": True, "min": 1, "max": 5},
        ],
    ),
)


def _demo_approver(actor: User) -> User:
    approver, created = User.objects.get_or_create(
        id=demo_import_uuid("user:import-approver"),
        defaults={
            "username": "aprobador_importaciones_demo",
            "email": "aprobador.importaciones@example.invalid",
            "first_name": "Aprobador",
            "last_name": "Sintético",
            "created_by": actor,
            "updated_by": actor,
        },
    )
    if created:
        approver.set_unusable_password()
        approver.save(update_fields=["password"])
    return approver


@transaction.atomic
def seed_import_templates(*, actor: User, dataset_version: str = "1") -> dict[str, int]:
    if dataset_version != "1":
        raise ValidationError("La versión de semilla de importaciones no está soportada.")
    organization = Organization.objects.filter(is_active=True).get()
    approver = _demo_approver(actor)
    for code, name, target_type, columns in TEMPLATE_CATALOG:
        template, _ = ImportTemplate.objects.get_or_create(
            id=demo_import_uuid(f"template:{code}"),
            defaults={
                "organization": organization,
                "code": code,
                "name": name,
                "target_type": target_type,
                "created_by": actor,
                "updated_by": actor,
            },
        )
        if template.organization_id != organization.pk:
            raise ValidationError("La semilla colisiona con una plantilla de otra organización.")
        template.code = code
        template.name = name
        template.target_type = target_type
        template.updated_by = actor
        template.full_clean()
        template.save(update_fields=["code", "name", "target_type", "updated_by", "updated_at"])
        normalized = normalize_schema({"columns": columns})
        digest = schema_hash(normalized)
        version, created = ImportTemplateVersion.objects.get_or_create(
            id=demo_import_uuid(f"template-version:{code}:1"),
            defaults={
                "template": template,
                "version_no": 1,
                "status": TemplateVersionStatus.EFFECTIVE,
                "schema_definition": normalized,
                "schema_hash": digest,
                "valid_from": DEMO_VALID_FROM,
                "submitted_at": timezone.now(),
                "submitted_by": actor,
                "approved_at": timezone.now(),
                "approved_by": approver,
                "decision_reason": "Plantilla sintética inicial",
                "created_by": actor,
                "updated_by": actor,
            },
        )
        if not created and version.schema_hash != digest:
            raise ValidationError("La plantilla sembrada fue modificada fuera del contrato.")
    return {
        "templates": ImportTemplate.objects.filter(organization=organization).count(),
        "versions": ImportTemplateVersion.objects.filter(
            template__organization=organization
        ).count(),
    }
