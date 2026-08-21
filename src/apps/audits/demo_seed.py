from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.documents.models import FileAsset, ScanStatus
from apps.organizations.models import Organization

from .models import (
    AuditExecution,
    AuditExecutionStatus,
    AuditPlan,
    AuditPlanStatus,
    AuditResponse,
    AuditResponseResult,
    Checklist,
    ChecklistItem,
    ChecklistResponseType,
    ChecklistVersion,
    ChecklistVersionStatus,
    Finding,
    FindingEvidence,
    FindingImpact,
    FindingStatus,
    FindingType,
)
from .services import checklist_version_hash

DEMO_NAMESPACE = uuid.UUID("7d5b3f6e-c2a2-5f79-82ca-fba10be9d28b")
DEMO_CUTOFF = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def demo_audit_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


def _demo_user(*, actor: User, key: str, username: str, first_name: str) -> User:
    user, created = User.objects.get_or_create(
        id=demo_audit_uuid(f"user:{key}"),
        defaults={
            "username": username,
            "email": f"{username}@example.invalid",
            "first_name": first_name,
            "last_name": "Auditoría Sintética",
            "created_by": actor,
            "updated_by": actor,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


def _seed_checklists(
    *, actor: User, approver: User, organization: Organization
) -> list[ChecklistVersion]:
    versions: list[ChecklistVersion] = []
    for list_index in range(3):
        code = f"LST-AUD-{list_index + 1:02d}"
        checklist, _ = Checklist.objects.get_or_create(
            id=demo_audit_uuid(f"checklist:{code}"),
            defaults={
                "organization": organization,
                "code": code,
                "name": f"Lista Administrativa Sintética {list_index + 1:02d}",
                "created_by": actor,
                "updated_by": actor,
            },
        )
        version, _ = ChecklistVersion.objects.get_or_create(
            id=demo_audit_uuid(f"checklist-version:{code}:1"),
            defaults={
                "checklist": checklist,
                "version_no": 1,
                "status": ChecklistVersionStatus.EFFECTIVE,
                "version_hash": hashlib.sha256(f"{code}:pending".encode()).hexdigest(),
                "valid_from": date(2026, 1, 1),
                "submitted_at": DEMO_CUTOFF,
                "submitted_by": actor,
                "approved_at": DEMO_CUTOFF,
                "approved_by": approver,
                "decision_reason": "Lista sintética aprobada para demostración",
                "created_by": actor,
                "updated_by": actor,
            },
        )
        for position in range(1, 16):
            ChecklistItem.objects.get_or_create(
                id=demo_audit_uuid(f"checklist-item:{code}:{position}"),
                defaults={
                    "checklist_version": version,
                    "position": position,
                    "criterion": (
                        f"Criterio administrativo sintético {list_index + 1:02d}."
                        f"{position:02d}"
                    ),
                    "response_type": ChecklistResponseType.COMPLIANCE,
                    "is_required": True,
                    "created_by": actor,
                    "updated_by": actor,
                },
            )
        digest = checklist_version_hash(version=version)
        if version.version_hash != digest:
            version.version_hash = digest
            version.updated_by = actor
            version.full_clean()
            version.save(update_fields=["version_hash", "updated_by", "updated_at"])
        versions.append(version)
    return versions


def _evidence_asset(*, actor: User, plan_number: int) -> FileAsset:
    content = f"P12-DATOS-SINTETICOS-EVIDENCIA-{plan_number:02d}".encode()
    digest = hashlib.sha256(content).hexdigest()
    asset, _ = FileAsset.objects.get_or_create(
        id=demo_audit_uuid(f"evidence:{plan_number:02d}"),
        defaults={
            "storage_key": f"documents/audits/evidencia-sintetica-{plan_number:02d}.txt",
            "original_name": f"evidencia-sintetica-{plan_number:02d}.txt",
            "media_type": "text/plain",
            "size_bytes": len(content),
            "sha256": digest,
            "scan_status": ScanStatus.CLEAN,
            "synthetic_confirmed": True,
            "created_by": actor,
            "updated_by": actor,
        },
    )
    return asset


@transaction.atomic
def seed_audits(*, actor: User, dataset_version: str = "1") -> dict[str, int]:
    if dataset_version != "1":
        raise ValidationError("La versión de semilla de auditorías no está soportada.")
    organization = Organization.objects.filter(is_active=True).get()
    auditor = _demo_user(
        actor=actor,
        key="auditor",
        username="auditor_demo",
        first_name="Auditor",
    )
    approver = _demo_user(
        actor=actor,
        key="approver",
        username="aprobador_auditorias_demo",
        first_name="Aprobador",
    )
    versions = _seed_checklists(actor=actor, approver=approver, organization=organization)
    plan_ids: list[uuid.UUID] = []
    execution_ids: list[uuid.UUID] = []
    finding_ids: list[uuid.UUID] = []
    for plan_index in range(12):
        plan_number = plan_index + 1
        code = f"AUD-{plan_number:02d}"
        plan_id = demo_audit_uuid(f"plan:{code}")
        plan, _ = AuditPlan.objects.get_or_create(
            id=plan_id,
            defaults={
                "organization": organization,
                "code": code,
                "scope": f"Proceso administrativo sintético {plan_number:02d}",
                "criteria": "Criterios internos demostrativos; no acreditan cumplimiento.",
                "lead_auditor": auditor,
                "planned_start": date(2026, 1, 1) + timedelta(days=plan_index * 7),
                "planned_end": date(2026, 1, 3) + timedelta(days=plan_index * 7),
                "status": AuditPlanStatus.COMPLETED,
                "submitted_at": DEMO_CUTOFF,
                "submitted_by": actor,
                "approved_at": DEMO_CUTOFF,
                "approved_by": approver,
                "decision_reason": "Plan sintético aprobado",
                "created_by": actor,
                "updated_by": approver,
            },
        )
        plan_ids.append(plan.pk)
        version = versions[plan_index % len(versions)]
        execution_id = demo_audit_uuid(f"execution:{code}")
        execution, _ = AuditExecution.objects.get_or_create(
            id=execution_id,
            defaults={
                "audit_plan": plan,
                "checklist_version": version,
                "started_at": DEMO_CUTOFF + timedelta(days=plan_index),
                "completed_at": DEMO_CUTOFF + timedelta(days=plan_index, hours=4),
                "status": AuditExecutionStatus.COMPLETED,
                "submitted_at": DEMO_CUTOFF + timedelta(days=plan_index, hours=3),
                "submitted_by": auditor,
                "reviewed_at": DEMO_CUTOFF + timedelta(days=plan_index, hours=4),
                "reviewed_by": approver,
                "decision_reason": "Ejecución sintética revisada",
                "created_by": auditor,
                "updated_by": approver,
            },
        )
        execution_ids.append(execution.pk)
        items = list(version.items.order_by("position"))
        for item_index, item in enumerate(items):
            global_index = plan_index * 15 + item_index + 1
            response, _ = AuditResponse.objects.get_or_create(
                id=demo_audit_uuid(f"response:{global_index:03d}"),
                defaults={
                    "execution": execution,
                    "checklist_item": item,
                    "result": AuditResponseResult.NONCONFORM,
                    "observation": (
                        f"Desviación administrativa sintética {global_index:03d}."
                    ),
                    "responded_by": auditor,
                    "responded_at": DEMO_CUTOFF + timedelta(days=plan_index, hours=1),
                    "created_by": auditor,
                    "updated_by": auditor,
                },
            )
            finding_id = demo_audit_uuid(f"finding:{global_index:03d}")
            has_file = item_index == 0
            finding, _ = Finding.objects.get_or_create(
                id=finding_id,
                defaults={
                    "execution": execution,
                    "audit_response": response,
                    "code": f"HAL-{global_index:03d}",
                    "finding_type": FindingType.NONCONFORMITY,
                    "criterion": item.criterion,
                    "condition": (
                        f"Condición administrativa ficticia {global_index:03d}."
                    ),
                    "impact": FindingImpact.values[(global_index - 1) % 4],
                    "status": FindingStatus.OPEN,
                    "owner": actor,
                    "due_date": date(2026, 2, 1) + timedelta(days=global_index % 30),
                    "evidence_absence_reason": (
                        "Evidencia no adjunta en esta fila sintética de volumen."
                        if not has_file
                        else ""
                    ),
                    "created_by": auditor,
                    "updated_by": auditor,
                },
            )
            finding_ids.append(finding.pk)
            if has_file:
                asset = _evidence_asset(actor=actor, plan_number=plan_number)
                FindingEvidence.objects.get_or_create(
                    id=demo_audit_uuid(f"finding-evidence:{global_index:03d}"),
                    defaults={
                        "finding": finding,
                        "file_asset": asset,
                        "description": "Evidencia textual exclusivamente sintética.",
                        "created_by": auditor,
                        "updated_by": auditor,
                    },
                )
    return {
        "plans": AuditPlan.objects.filter(pk__in=plan_ids).count(),
        "executions": AuditExecution.objects.filter(pk__in=execution_ids).count(),
        "findings": Finding.objects.filter(pk__in=finding_ids).count(),
        "checklists": Checklist.objects.filter(organization=organization).count(),
        "responses": AuditResponse.objects.filter(execution_id__in=execution_ids).count(),
        "evidence": FindingEvidence.objects.filter(finding_id__in=finding_ids).count(),
    }
