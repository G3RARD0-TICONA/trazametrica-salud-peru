from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audits.models import Finding, FindingStatus, FindingType
from apps.documents.models import FileAsset, ScanStatus

from .models import (
    ActionEvidence,
    CorrectiveAction,
    CorrectiveActionStatus,
    EffectivenessResult,
    EffectivenessReview,
    RootCauseAnalysis,
    RootCauseMethod,
    RootCauseStatus,
)

DEMO_NAMESPACE = uuid.UUID("27e570a1-6d2e-5c4d-8b85-f6671dfb1b3a")
DEMO_CUTOFF = datetime(2026, 2, 15, 12, 0, tzinfo=UTC)


def demo_improvement_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


def _demo_user(*, actor: User, key: str, username: str, first_name: str) -> User:
    user, created = User.objects.get_or_create(
        id=demo_improvement_uuid(f"user:{key}"),
        defaults={
            "username": username,
            "email": f"{username}@example.invalid",
            "first_name": first_name,
            "last_name": "Mejora Sintética",
            "created_by": actor,
            "updated_by": actor,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


def _evidence_asset(*, actor: User, action_number: int) -> FileAsset:
    content = f"P13-DATOS-SINTETICOS-ACCION-{action_number:03d}".encode()
    digest = hashlib.sha256(content).hexdigest()
    asset, _ = FileAsset.objects.get_or_create(
        id=demo_improvement_uuid(f"evidence:{action_number:03d}"),
        defaults={
            "storage_key": (
                f"documents/improvements/evidencia-accion-{action_number:03d}.txt"
            ),
            "original_name": f"evidencia-accion-{action_number:03d}.txt",
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
def seed_improvements(*, actor: User, dataset_version: str = "1") -> dict[str, int]:
    if dataset_version != "1":
        raise ValidationError("La versión de semilla de mejora no está soportada.")
    findings = list(
        Finding.objects.filter(finding_type=FindingType.NONCONFORMITY)
        .exclude(status=FindingStatus.CANCELLED)
        .order_by("code")[:12]
    )
    if len(findings) != 12:
        raise ValidationError("Ejecute primero la semilla P12 de auditorías.")
    owner = _demo_user(
        actor=actor,
        key="owner",
        username="responsable_capa_demo",
        first_name="Responsable",
    )
    reviewer = _demo_user(
        actor=actor,
        key="reviewer",
        username="verificador_capa_demo",
        first_name="Verificador",
    )
    cause_ids: list[uuid.UUID] = []
    action_ids: list[uuid.UUID] = []
    review_ids: list[uuid.UUID] = []
    evidence_ids: list[uuid.UUID] = []
    for finding_index, finding in enumerate(findings):
        cause_id = demo_improvement_uuid(f"root-cause:{finding.code}")
        cause, _ = RootCauseAnalysis.objects.get_or_create(
            id=cause_id,
            defaults={
                "finding": finding,
                "method": RootCauseMethod.FIVE_WHYS,
                "analysis": f"Análisis causal sintético del hallazgo {finding.code}.",
                "conclusion": (
                    f"Causa administrativa ficticia controlable {finding_index + 1:02d}."
                ),
                "status": RootCauseStatus.APPROVED,
                "submitted_at": DEMO_CUTOFF,
                "submitted_by": actor,
                "approved_at": DEMO_CUTOFF,
                "approved_by": reviewer,
                "decision_reason": "Causa sintética aprobada para demostración.",
                "created_by": actor,
                "updated_by": reviewer,
            },
        )
        cause_ids.append(cause.pk)
        for action_offset in range(2):
            action_number = finding_index * 2 + action_offset + 1
            if finding_index < 6:
                status = CorrectiveActionStatus.CLOSED
                review_result = EffectivenessResult.EFFECTIVE
            elif finding_index < 9 and action_offset == 0:
                status = CorrectiveActionStatus.REOPENED
                review_result = EffectivenessResult.INEFFECTIVE
            elif finding_index >= 9 and action_offset == 0:
                status = CorrectiveActionStatus.IN_VERIFICATION
                review_result = None
            else:
                status = CorrectiveActionStatus.IN_PROGRESS
                review_result = None
            has_evidence = status in {
                CorrectiveActionStatus.CLOSED,
                CorrectiveActionStatus.REOPENED,
                CorrectiveActionStatus.IN_VERIFICATION,
            }
            completed = has_evidence
            action_id = demo_improvement_uuid(f"action:{action_number:03d}")
            action, _ = CorrectiveAction.objects.get_or_create(
                id=action_id,
                defaults={
                    "finding": finding,
                    "root_cause": cause,
                    "code": f"ACP-{action_number:03d}",
                    "description": (
                        f"Acción administrativa sintética {action_number:03d}."
                    ),
                    "owner": owner,
                    "due_date": date(2026, 3, 1) + timedelta(days=action_number),
                    "status": status,
                    "effectiveness_criterion": (
                        "Evidencia sintética revisada y ausencia de recurrencia ficticia."
                    ),
                    "is_mandatory": True,
                    "submitted_at": DEMO_CUTOFF,
                    "submitted_by": actor,
                    "approved_at": DEMO_CUTOFF,
                    "approved_by": reviewer,
                    "completed_at": (
                        DEMO_CUTOFF + timedelta(days=action_number) if completed else None
                    ),
                    "completed_by": owner if completed else None,
                    "decision_reason": "Plan sintético aprobado.",
                    "created_by": actor,
                    "updated_by": reviewer,
                },
            )
            action_ids.append(action.pk)
            if has_evidence:
                asset = _evidence_asset(actor=actor, action_number=action_number)
                evidence, _ = ActionEvidence.objects.get_or_create(
                    id=demo_improvement_uuid(f"action-evidence:{action_number:03d}"),
                    defaults={
                        "action": action,
                        "file_asset": asset,
                        "description": "Evidencia textual exclusivamente sintética.",
                        "created_by": owner,
                        "updated_by": owner,
                    },
                )
                evidence_ids.append(evidence.pk)
            if review_result is not None:
                review, _ = EffectivenessReview.objects.get_or_create(
                    id=demo_improvement_uuid(f"review:{action_number:03d}"),
                    defaults={
                        "action": action,
                        "reviewer": reviewer,
                        "reviewed_at": DEMO_CUTOFF + timedelta(days=action_number, hours=2),
                        "result": review_result,
                        "notes": (
                            "Resultado sintético eficaz."
                            if review_result == EffectivenessResult.EFFECTIVE
                            else "Resultado sintético no eficaz; requiere reapertura."
                        ),
                        "reopens_action": (
                            review_result == EffectivenessResult.INEFFECTIVE
                        ),
                        "created_by": reviewer,
                        "updated_by": reviewer,
                    },
                )
                review_ids.append(review.pk)
        finding.status = (
            FindingStatus.CLOSED
            if finding_index < 6
            else FindingStatus.REOPENED
            if finding_index < 9
            else FindingStatus.IN_VERIFICATION
        )
        finding.updated_by = reviewer
        finding.full_clean()
        finding.save(update_fields=["status", "updated_by", "updated_at"])
    return {
        "root_causes": RootCauseAnalysis.objects.filter(pk__in=cause_ids).count(),
        "actions": CorrectiveAction.objects.filter(pk__in=action_ids).count(),
        "evidence": ActionEvidence.objects.filter(pk__in=evidence_ids).count(),
        "reviews": EffectivenessReview.objects.filter(pk__in=review_ids).count(),
    }
