from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import date, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.auditlog.models import EventResult
from apps.auditlog.services import record_event
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


def _require(actor: User, capability: Capability) -> None:
    if not actor.is_active or not has_capability(actor, capability):
        raise PermissionDenied("El actor no cuenta con la capacidad de auditoría requerida.")


def _require_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized:
        raise ValidationError("La decisión requiere un motivo.")
    return normalized


def checklist_version_hash(*, version: ChecklistVersion) -> str:
    payload = {
        "checklist_id": str(version.checklist_id),
        "items": [
            {
                "criterion": item.criterion.strip(),
                "is_required": item.is_required,
                "position": item.position,
                "response_type": item.response_type,
            }
            for item in version.items.order_by("position", "id")
        ],
        "version_no": version.version_no,
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _refresh_checklist_hash(*, actor: User, version: ChecklistVersion) -> None:
    version.version_hash = checklist_version_hash(version=version)
    version.updated_by = actor
    version.full_clean()
    version.save(update_fields=["version_hash", "updated_by", "updated_at"])


@transaction.atomic
def create_audit_plan(
    *,
    actor: User,
    organization: Organization,
    code: str,
    scope: str,
    criteria: str,
    lead_auditor: User,
    planned_start: date,
    planned_end: date,
) -> AuditPlan:
    _require(actor, Capability.PLAN_AUDITS)
    if not organization.is_active or not lead_auditor.is_active:
        raise ValidationError("La organización y el auditor deben estar activos.")
    plan = AuditPlan(
        organization=organization,
        code=code,
        scope=scope,
        criteria=criteria,
        lead_auditor=lead_auditor,
        planned_start=planned_start,
        planned_end=planned_end,
        status=AuditPlanStatus.DRAFT,
        created_by=actor,
        updated_by=actor,
    )
    plan.full_clean()
    plan.save()
    record_event(
        actor=actor,
        object_type="audits.AuditPlan",
        object_id=plan.pk,
        action="audit_plan.created",
        result=EventResult.SUCCESS,
        context={"code": plan.code, "lead_auditor_id": str(lead_auditor.pk)},
    )
    return plan


@transaction.atomic
def update_audit_plan(
    *,
    actor: User,
    plan: AuditPlan,
    scope: str,
    criteria: str,
    lead_auditor: User,
    planned_start: date,
    planned_end: date,
) -> AuditPlan:
    _require(actor, Capability.PLAN_AUDITS)
    locked = AuditPlan.objects.select_for_update().get(pk=plan.pk)
    if locked.status != AuditPlanStatus.DRAFT:
        raise ValidationError("Solo un plan en borrador puede editarse.")
    locked.scope = scope
    locked.criteria = criteria
    locked.lead_auditor = lead_auditor
    locked.planned_start = planned_start
    locked.planned_end = planned_end
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "scope",
            "criteria",
            "lead_auditor",
            "planned_start",
            "planned_end",
            "updated_by",
            "updated_at",
        ]
    )
    return locked


@transaction.atomic
def submit_audit_plan(*, actor: User, plan: AuditPlan) -> AuditPlan:
    _require(actor, Capability.PLAN_AUDITS)
    locked = AuditPlan.objects.select_for_update().get(pk=plan.pk)
    if locked.status != AuditPlanStatus.DRAFT:
        raise ValidationError("Solo un plan en borrador puede enviarse a revisión.")
    locked.status = AuditPlanStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "submitted_at", "submitted_by", "updated_by", "updated_at"]
    )
    record_event(
        actor=actor,
        object_type="audits.AuditPlan",
        object_id=locked.pk,
        action="audit_plan.submitted",
        result=EventResult.SUCCESS,
        context={},
    )
    return locked


@transaction.atomic
def reject_audit_plan(*, actor: User, plan: AuditPlan, reason: str) -> AuditPlan:
    _require(actor, Capability.APPROVE_AUDITS)
    normalized = _require_reason(reason)
    locked = AuditPlan.objects.select_for_update().get(pk=plan.pk)
    if locked.status != AuditPlanStatus.IN_REVIEW:
        raise ValidationError("Solo un plan en revisión puede rechazarse.")
    if locked.submitted_by_id == actor.pk:
        raise PermissionDenied("El autor del envío no puede decidir su propio plan.")
    locked.status = AuditPlanStatus.DRAFT
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "decision_reason", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="audits.AuditPlan",
        object_id=locked.pk,
        action="audit_plan.rejected",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={},
    )
    return locked


@transaction.atomic
def approve_audit_plan(*, actor: User, plan: AuditPlan, reason: str) -> AuditPlan:
    _require(actor, Capability.APPROVE_AUDITS)
    normalized = _require_reason(reason)
    locked = AuditPlan.objects.select_for_update().get(pk=plan.pk)
    if locked.status != AuditPlanStatus.IN_REVIEW:
        raise ValidationError("Solo un plan en revisión puede aprobarse.")
    if locked.submitted_by_id == actor.pk or locked.created_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propio plan.")
    now = timezone.now()
    locked.status = AuditPlanStatus.APPROVED
    locked.approved_at = now
    locked.approved_by = actor
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "approved_at",
            "approved_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="audits.AuditPlan",
        object_id=locked.pk,
        action="audit_plan.approved",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={},
    )
    return locked


@transaction.atomic
def create_checklist(
    *, actor: User, organization: Organization, code: str, name: str
) -> Checklist:
    _require(actor, Capability.PLAN_AUDITS)
    if not organization.is_active:
        raise ValidationError("La organización debe estar activa.")
    checklist = Checklist(
        organization=organization,
        code=code,
        name=name,
        created_by=actor,
        updated_by=actor,
    )
    checklist.full_clean()
    checklist.save()
    record_event(
        actor=actor,
        object_type="audits.Checklist",
        object_id=checklist.pk,
        action="audit_checklist.created",
        result=EventResult.SUCCESS,
        context={"code": checklist.code},
    )
    return checklist


@transaction.atomic
def create_checklist_version(*, actor: User, checklist: Checklist) -> ChecklistVersion:
    _require(actor, Capability.PLAN_AUDITS)
    locked = Checklist.objects.select_for_update().get(pk=checklist.pk)
    if not locked.is_active:
        raise ValidationError("La lista debe estar activa.")
    version_no = int(locked.versions.aggregate(max_no=Max("version_no"))["max_no"] or 0) + 1
    placeholder_hash = hashlib.sha256(
        f"{locked.pk}:{version_no}:empty".encode()
    ).hexdigest()
    version = ChecklistVersion(
        checklist=locked,
        version_no=version_no,
        status=ChecklistVersionStatus.DRAFT,
        version_hash=placeholder_hash,
        created_by=actor,
        updated_by=actor,
    )
    version.full_clean()
    version.save()
    _refresh_checklist_hash(actor=actor, version=version)
    return version


@transaction.atomic
def add_checklist_item(
    *,
    actor: User,
    version: ChecklistVersion,
    criterion: str,
    response_type: ChecklistResponseType,
    is_required: bool = True,
) -> ChecklistItem:
    _require(actor, Capability.PLAN_AUDITS)
    locked = ChecklistVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != ChecklistVersionStatus.DRAFT:
        raise ValidationError("Solo se agregan criterios a una lista en borrador.")
    position = int(locked.items.aggregate(max_no=Max("position"))["max_no"] or 0) + 1
    item = ChecklistItem(
        checklist_version=locked,
        position=position,
        criterion=criterion,
        response_type=response_type,
        is_required=is_required,
        created_by=actor,
        updated_by=actor,
    )
    item.full_clean()
    item.save()
    _refresh_checklist_hash(actor=actor, version=locked)
    return item


@transaction.atomic
def submit_checklist_version(
    *, actor: User, version: ChecklistVersion
) -> ChecklistVersion:
    _require(actor, Capability.PLAN_AUDITS)
    locked = ChecklistVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != ChecklistVersionStatus.DRAFT:
        raise ValidationError("Solo una lista en borrador puede enviarse a revisión.")
    if not locked.items.filter(is_required=True).exists():
        raise ValidationError("La lista requiere al menos un criterio obligatorio.")
    digest = checklist_version_hash(version=locked)
    if digest != locked.version_hash:
        raise ValidationError("La lista fue modificada fuera del flujo controlado.")
    locked.status = ChecklistVersionStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "submitted_at", "submitted_by", "updated_by", "updated_at"]
    )
    return locked


@transaction.atomic
def approve_checklist_version(
    *, actor: User, version: ChecklistVersion, valid_from: date, reason: str
) -> ChecklistVersion:
    _require(actor, Capability.APPROVE_AUDITS)
    normalized = _require_reason(reason)
    locked = (
        ChecklistVersion.objects.select_for_update()
        .select_related("checklist")
        .get(pk=version.pk)
    )
    if locked.status != ChecklistVersionStatus.IN_REVIEW:
        raise ValidationError("Solo una lista en revisión puede aprobarse.")
    if locked.submitted_by_id == actor.pk or locked.created_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propia lista.")
    if checklist_version_hash(version=locked) != locked.version_hash:
        raise ValidationError("El contenido no coincide con el hash enviado.")
    prior_versions = list(
        ChecklistVersion.objects.select_for_update().filter(
            checklist=locked.checklist,
            status=ChecklistVersionStatus.EFFECTIVE,
        )
    )
    for prior in prior_versions:
        if prior.valid_from is not None and valid_from <= prior.valid_from:
            raise ValidationError("La nueva vigencia debe iniciar después de la vigente.")
        prior.status = ChecklistVersionStatus.SUPERSEDED
        prior.valid_to = valid_from - timedelta(days=1)
        prior.updated_by = actor
        prior.full_clean()
        prior.save(update_fields=["status", "valid_to", "updated_by", "updated_at"])
    now = timezone.now()
    locked.status = ChecklistVersionStatus.EFFECTIVE
    locked.valid_from = valid_from
    locked.approved_at = now
    locked.approved_by = actor
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "valid_from",
            "approved_at",
            "approved_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="audits.ChecklistVersion",
        object_id=locked.pk,
        action="audit_checklist_version.approved",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def start_audit_execution(
    *, actor: User, plan: AuditPlan, checklist_version: ChecklistVersion
) -> AuditExecution:
    _require(actor, Capability.EXECUTE_AUDITS)
    locked_plan = AuditPlan.objects.select_for_update().get(pk=plan.pk)
    locked_version = (
        ChecklistVersion.objects.select_for_update()
        .select_related("checklist")
        .get(pk=checklist_version.pk)
    )
    if locked_plan.status != AuditPlanStatus.APPROVED:
        raise ValidationError("El plan debe estar aprobado antes de ejecutarse.")
    if locked_version.status != ChecklistVersionStatus.EFFECTIVE:
        raise ValidationError("La lista debe estar vigente.")
    if locked_version.checklist.organization_id != locked_plan.organization_id:
        raise ValidationError("La lista pertenece a otra organización.")
    if locked_plan.executions.exists():
        raise ValidationError("El plan ya cuenta con una ejecución.")
    now = timezone.now()
    execution = AuditExecution(
        audit_plan=locked_plan,
        checklist_version=locked_version,
        started_at=now,
        status=AuditExecutionStatus.IN_PROGRESS,
        created_by=actor,
        updated_by=actor,
    )
    execution.full_clean()
    execution.save()
    locked_plan.status = AuditPlanStatus.IN_PROGRESS
    locked_plan.updated_by = actor
    locked_plan.full_clean()
    locked_plan.save(update_fields=["status", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="audits.AuditExecution",
        object_id=execution.pk,
        action="audit_execution.started",
        result=EventResult.SUCCESS,
        context={"plan_id": str(locked_plan.pk)},
    )
    return execution


@transaction.atomic
def record_audit_response(
    *,
    actor: User,
    execution: AuditExecution,
    checklist_item: ChecklistItem,
    result: AuditResponseResult,
    observation: str = "",
) -> AuditResponse:
    _require(actor, Capability.EXECUTE_AUDITS)
    locked_execution = AuditExecution.objects.select_for_update().get(pk=execution.pk)
    if locked_execution.status != AuditExecutionStatus.IN_PROGRESS:
        raise ValidationError("Las respuestas solo se registran durante la ejecución.")
    if checklist_item.checklist_version_id != locked_execution.checklist_version_id:
        raise ValidationError("El criterio no pertenece a la lista ejecutada.")
    response = AuditResponse.objects.filter(
        execution=locked_execution, checklist_item=checklist_item
    ).first()
    if response is None:
        response = AuditResponse(
            execution=locked_execution,
            checklist_item=checklist_item,
            created_by=actor,
            updated_by=actor,
            responded_by=actor,
            responded_at=timezone.now(),
        )
    response.result = result
    response.observation = observation
    response.responded_by = actor
    response.responded_at = timezone.now()
    response.updated_by = actor
    response.full_clean()
    response.save()
    return response


@transaction.atomic
def create_finding(
    *,
    actor: User,
    execution: AuditExecution,
    code: str,
    finding_type: FindingType,
    criterion: str,
    condition: str,
    impact: FindingImpact,
    owner: User,
    due_date: date,
    audit_response: AuditResponse | None = None,
    evidence: Sequence[tuple[FileAsset, str]] = (),
    evidence_absence_reason: str = "",
) -> Finding:
    _require(actor, Capability.EXECUTE_AUDITS)
    locked_execution = AuditExecution.objects.select_for_update().get(pk=execution.pk)
    if locked_execution.status != AuditExecutionStatus.IN_PROGRESS:
        raise ValidationError("El hallazgo requiere una auditoría en ejecución.")
    normalized_absence = evidence_absence_reason.strip()
    if not evidence and not normalized_absence:
        raise ValidationError("El hallazgo requiere evidencia o justificación de ausencia.")
    if audit_response is not None and audit_response.execution_id != locked_execution.pk:
        raise ValidationError("La respuesta pertenece a otra ejecución.")
    if not owner.is_active:
        raise ValidationError("El responsable debe estar activo.")
    for asset, description in evidence:
        if asset.scan_status != ScanStatus.CLEAN or not asset.synthetic_confirmed:
            raise ValidationError("La evidencia debe ser sintética y estar validada.")
        if not description.strip():
            raise ValidationError("Cada evidencia requiere descripción.")
    finding = Finding(
        execution=locked_execution,
        audit_response=audit_response,
        code=code,
        finding_type=finding_type,
        criterion=criterion,
        condition=condition,
        impact=impact,
        status=FindingStatus.OPEN,
        owner=owner,
        due_date=due_date,
        evidence_absence_reason=normalized_absence,
        created_by=actor,
        updated_by=actor,
    )
    finding.full_clean()
    finding.save()
    for asset, description in evidence:
        link = FindingEvidence(
            finding=finding,
            file_asset=asset,
            description=description,
            created_by=actor,
            updated_by=actor,
        )
        link.full_clean()
        link.save()
    record_event(
        actor=actor,
        object_type="audits.Finding",
        object_id=finding.pk,
        action="audit_finding.created",
        result=EventResult.SUCCESS,
        context={
            "code": finding.code,
            "evidence_count": len(evidence),
            "finding_type": finding.finding_type,
        },
    )
    return finding


@transaction.atomic
def cancel_finding(*, actor: User, finding: Finding, reason: str) -> Finding:
    _require(actor, Capability.REVIEW_AUDITS)
    normalized = _require_reason(reason)
    locked = Finding.objects.select_for_update().get(pk=finding.pk)
    if locked.status == FindingStatus.CANCELLED:
        raise ValidationError("El hallazgo ya está cancelado.")
    locked.status = FindingStatus.CANCELLED
    locked.cancellation_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "cancellation_reason", "updated_by", "updated_at"]
    )
    record_event(
        actor=actor,
        object_type="audits.Finding",
        object_id=locked.pk,
        action="audit_finding.cancelled",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={},
    )
    return locked


@transaction.atomic
def submit_execution_review(
    *, actor: User, execution: AuditExecution
) -> AuditExecution:
    _require(actor, Capability.EXECUTE_AUDITS)
    locked = AuditExecution.objects.select_for_update().get(pk=execution.pk)
    if locked.status != AuditExecutionStatus.IN_PROGRESS:
        raise ValidationError("Solo una ejecución activa puede enviarse a revisión.")
    required_ids = set(
        locked.checklist_version.items.filter(is_required=True).values_list("id", flat=True)
    )
    answered_ids = set(locked.responses.values_list("checklist_item_id", flat=True))
    if not required_ids.issubset(answered_ids):
        raise ValidationError("Todos los criterios obligatorios deben responderse.")
    nonconform_response_ids = set(
        locked.responses.filter(result=AuditResponseResult.NONCONFORM).values_list(
            "id", flat=True
        )
    )
    finding_response_ids = set(
        locked.findings.exclude(status=FindingStatus.CANCELLED)
        .exclude(audit_response__isnull=True)
        .values_list("audit_response_id", flat=True)
    )
    if not nonconform_response_ids.issubset(finding_response_ids):
        raise ValidationError("Cada respuesta no conforme requiere un hallazgo vigente.")
    locked.status = AuditExecutionStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "submitted_at", "submitted_by", "updated_by", "updated_at"]
    )
    return locked


@transaction.atomic
def reject_execution(
    *, actor: User, execution: AuditExecution, reason: str
) -> AuditExecution:
    _require(actor, Capability.REVIEW_AUDITS)
    normalized = _require_reason(reason)
    locked = AuditExecution.objects.select_for_update().get(pk=execution.pk)
    if locked.status != AuditExecutionStatus.IN_REVIEW:
        raise ValidationError("Solo una ejecución en revisión puede rechazarse.")
    if locked.submitted_by_id == actor.pk:
        raise PermissionDenied("Quien envió la ejecución no puede revisar su propio trabajo.")
    locked.status = AuditExecutionStatus.IN_PROGRESS
    locked.decision_reason = normalized
    locked.reviewed_at = timezone.now()
    locked.reviewed_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "decision_reason",
            "reviewed_at",
            "reviewed_by",
            "updated_by",
            "updated_at",
        ]
    )
    return locked


@transaction.atomic
def approve_execution(
    *, actor: User, execution: AuditExecution, reason: str
) -> AuditExecution:
    _require(actor, Capability.APPROVE_AUDITS)
    normalized = _require_reason(reason)
    locked = (
        AuditExecution.objects.select_for_update()
        .select_related("audit_plan")
        .get(pk=execution.pk)
    )
    if locked.status != AuditExecutionStatus.IN_REVIEW:
        raise ValidationError("Solo una ejecución en revisión puede aprobarse.")
    if locked.submitted_by_id == actor.pk or locked.audit_plan.lead_auditor_id == actor.pk:
        raise PermissionDenied("El auditor no puede aprobar el cierre de su ejecución.")
    now = timezone.now()
    locked.status = AuditExecutionStatus.COMPLETED
    locked.completed_at = now
    locked.reviewed_at = now
    locked.reviewed_by = actor
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "completed_at",
            "reviewed_at",
            "reviewed_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    plan = AuditPlan.objects.select_for_update().get(pk=locked.audit_plan_id)
    plan.status = AuditPlanStatus.COMPLETED
    plan.updated_by = actor
    plan.full_clean()
    plan.save(update_fields=["status", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="audits.AuditExecution",
        object_id=locked.pk,
        action="audit_execution.completed",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"finding_count": locked.findings.count()},
    )
    return locked
