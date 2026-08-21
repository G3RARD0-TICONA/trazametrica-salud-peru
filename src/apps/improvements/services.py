from __future__ import annotations

from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.auditlog.models import EventResult
from apps.auditlog.services import record_event
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


def _require(actor: User, capability: Capability) -> None:
    if not actor.is_active or not has_capability(actor, capability):
        raise PermissionDenied("El actor no cuenta con la capacidad de mejora requerida.")


def _require_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized:
        raise ValidationError("La decisión requiere un motivo.")
    return normalized


def _set_finding_status(*, finding: Finding, status: FindingStatus, actor: User) -> None:
    finding.status = status
    finding.updated_by = actor
    finding.full_clean()
    finding.save(update_fields=["status", "updated_by", "updated_at"])


def _validate_open_finding(finding: Finding) -> None:
    if finding.finding_type != FindingType.NONCONFORMITY:
        raise ValidationError("P13 requiere una no conformidad para iniciar CAPA.")
    if finding.status in {FindingStatus.CANCELLED, FindingStatus.CLOSED}:
        raise ValidationError("El hallazgo cerrado o cancelado no admite cambios CAPA.")


@transaction.atomic
def create_root_cause_analysis(
    *,
    actor: User,
    finding: Finding,
    method: RootCauseMethod,
    analysis: str,
    conclusion: str,
) -> RootCauseAnalysis:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    locked_finding = Finding.objects.select_for_update().get(pk=finding.pk)
    _validate_open_finding(locked_finding)
    if RootCauseAnalysis.objects.filter(finding=locked_finding).exists():
        raise ValidationError("El hallazgo ya cuenta con un análisis causal.")
    root_cause = RootCauseAnalysis(
        finding=locked_finding,
        method=method,
        analysis=analysis,
        conclusion=conclusion,
        status=RootCauseStatus.DRAFT,
        created_by=actor,
        updated_by=actor,
    )
    root_cause.full_clean()
    root_cause.save()
    _set_finding_status(
        finding=locked_finding, status=FindingStatus.IN_ANALYSIS, actor=actor
    )
    record_event(
        actor=actor,
        object_type="improvements.RootCauseAnalysis",
        object_id=root_cause.pk,
        action="root_cause.created",
        result=EventResult.SUCCESS,
        context={"finding_id": str(locked_finding.pk), "method": root_cause.method},
    )
    return root_cause


@transaction.atomic
def update_root_cause_analysis(
    *,
    actor: User,
    root_cause: RootCauseAnalysis,
    method: RootCauseMethod,
    analysis: str,
    conclusion: str,
) -> RootCauseAnalysis:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    locked = RootCauseAnalysis.objects.select_for_update().get(pk=root_cause.pk)
    if locked.status != RootCauseStatus.DRAFT:
        raise ValidationError("Solo una causa en borrador puede editarse.")
    locked.method = method
    locked.analysis = analysis
    locked.conclusion = conclusion
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["method", "analysis", "conclusion", "updated_by", "updated_at"]
    )
    return locked


@transaction.atomic
def submit_root_cause_analysis(
    *, actor: User, root_cause: RootCauseAnalysis
) -> RootCauseAnalysis:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    locked = RootCauseAnalysis.objects.select_for_update().get(pk=root_cause.pk)
    if locked.status != RootCauseStatus.DRAFT:
        raise ValidationError("Solo una causa en borrador puede enviarse a revisión.")
    locked.status = RootCauseStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "submitted_at", "submitted_by", "updated_by", "updated_at"]
    )
    return locked


@transaction.atomic
def reject_root_cause_analysis(
    *, actor: User, root_cause: RootCauseAnalysis, reason: str
) -> RootCauseAnalysis:
    _require(actor, Capability.APPROVE_IMPROVEMENTS)
    normalized = _require_reason(reason)
    locked = RootCauseAnalysis.objects.select_for_update().get(pk=root_cause.pk)
    if locked.status != RootCauseStatus.IN_REVIEW:
        raise ValidationError("Solo una causa en revisión puede rechazarse.")
    if locked.submitted_by_id == actor.pk:
        raise PermissionDenied("Quien envió la causa no puede decidir su propio análisis.")
    locked.status = RootCauseStatus.DRAFT
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "decision_reason", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="improvements.RootCauseAnalysis",
        object_id=locked.pk,
        action="root_cause.rejected",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={},
    )
    return locked


@transaction.atomic
def approve_root_cause_analysis(
    *, actor: User, root_cause: RootCauseAnalysis, reason: str
) -> RootCauseAnalysis:
    _require(actor, Capability.APPROVE_IMPROVEMENTS)
    normalized = _require_reason(reason)
    locked = RootCauseAnalysis.objects.select_for_update().get(pk=root_cause.pk)
    if locked.status != RootCauseStatus.IN_REVIEW:
        raise ValidationError("Solo una causa en revisión puede aprobarse.")
    if locked.created_by_id == actor.pk or locked.submitted_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propio análisis causal.")
    locked.status = RootCauseStatus.APPROVED
    locked.approved_at = timezone.now()
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
        object_type="improvements.RootCauseAnalysis",
        object_id=locked.pk,
        action="root_cause.approved",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"finding_id": str(locked.finding_id)},
    )
    return locked


@transaction.atomic
def create_corrective_action(
    *,
    actor: User,
    root_cause: RootCauseAnalysis,
    code: str,
    description: str,
    owner: User,
    due_date: date,
    effectiveness_criterion: str,
    is_mandatory: bool = True,
) -> CorrectiveAction:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    locked_cause = (
        RootCauseAnalysis.objects.select_for_update()
        .select_related("finding")
        .get(pk=root_cause.pk)
    )
    _validate_open_finding(locked_cause.finding)
    if locked_cause.status != RootCauseStatus.APPROVED:
        raise ValidationError("RN-015: la causa debe aprobarse antes de crear el plan.")
    if not owner.is_active:
        raise ValidationError("La acción requiere un responsable activo.")
    action = CorrectiveAction(
        finding=locked_cause.finding,
        root_cause=locked_cause,
        code=code,
        description=description,
        owner=owner,
        due_date=due_date,
        status=CorrectiveActionStatus.PENDING,
        effectiveness_criterion=effectiveness_criterion,
        is_mandatory=is_mandatory,
        created_by=actor,
        updated_by=actor,
    )
    action.full_clean()
    action.save()
    record_event(
        actor=actor,
        object_type="improvements.CorrectiveAction",
        object_id=action.pk,
        action="corrective_action.created",
        result=EventResult.SUCCESS,
        context={"finding_id": str(action.finding_id), "owner_id": str(owner.pk)},
    )
    return action


@transaction.atomic
def submit_corrective_action(
    *, actor: User, action: CorrectiveAction
) -> CorrectiveAction:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    locked = (
        CorrectiveAction.objects.select_for_update()
        .select_related("root_cause", "owner")
        .get(pk=action.pk)
    )
    if locked.status != CorrectiveActionStatus.PENDING:
        raise ValidationError("Solo una acción pendiente puede enviarse a revisión.")
    if locked.root_cause.status != RootCauseStatus.APPROVED:
        raise ValidationError("RN-015: la acción requiere una causa aprobada.")
    if not locked.owner.is_active:
        raise ValidationError("RN-016: la acción requiere un responsable activo.")
    locked.status = CorrectiveActionStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "submitted_at", "submitted_by", "updated_by", "updated_at"]
    )
    return locked


@transaction.atomic
def reject_corrective_action(
    *, actor: User, action: CorrectiveAction, reason: str
) -> CorrectiveAction:
    _require(actor, Capability.APPROVE_IMPROVEMENTS)
    normalized = _require_reason(reason)
    locked = CorrectiveAction.objects.select_for_update().get(pk=action.pk)
    if locked.status != CorrectiveActionStatus.IN_REVIEW:
        raise ValidationError("Solo una acción en revisión puede rechazarse.")
    if locked.submitted_by_id == actor.pk:
        raise PermissionDenied("Quien envió la acción no puede decidirla.")
    locked.status = CorrectiveActionStatus.PENDING
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "decision_reason", "updated_by", "updated_at"])
    return locked


@transaction.atomic
def approve_corrective_action(
    *, actor: User, action: CorrectiveAction, reason: str
) -> CorrectiveAction:
    _require(actor, Capability.APPROVE_IMPROVEMENTS)
    normalized = _require_reason(reason)
    locked = (
        CorrectiveAction.objects.select_for_update()
        .select_related("root_cause", "finding", "owner")
        .get(pk=action.pk)
    )
    if locked.status != CorrectiveActionStatus.IN_REVIEW:
        raise ValidationError("Solo una acción en revisión puede aprobarse.")
    if locked.created_by_id == actor.pk or locked.submitted_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propia acción.")
    if locked.root_cause.status != RootCauseStatus.APPROVED:
        raise ValidationError("RN-015: el plan requiere una causa aprobada.")
    if not locked.owner.is_active:
        raise ValidationError("RN-016: la acción requiere un responsable activo.")
    locked.status = CorrectiveActionStatus.IN_PROGRESS
    locked.approved_at = timezone.now()
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
    _set_finding_status(
        finding=locked.finding, status=FindingStatus.WITH_PLAN, actor=actor
    )
    record_event(
        actor=actor,
        object_type="improvements.CorrectiveAction",
        object_id=locked.pk,
        action="corrective_action.approved",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"finding_id": str(locked.finding_id)},
    )
    return locked


@transaction.atomic
def reassign_corrective_action(
    *, actor: User, action: CorrectiveAction, new_owner: User, reason: str
) -> CorrectiveAction:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    normalized = _require_reason(reason)
    if not new_owner.is_active:
        raise ValidationError("El nuevo responsable debe estar activo.")
    locked = CorrectiveAction.objects.select_for_update().get(pk=action.pk)
    if locked.status in {CorrectiveActionStatus.CLOSED, CorrectiveActionStatus.CANCELLED}:
        raise ValidationError("La acción cerrada o cancelada no puede reasignarse.")
    prior_owner_id = locked.owner_id
    locked.owner = new_owner
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["owner", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="improvements.CorrectiveAction",
        object_id=locked.pk,
        action="corrective_action.reassigned",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={
            "new_owner_id": str(new_owner.pk),
            "prior_owner_id": str(prior_owner_id),
        },
    )
    return locked


@transaction.atomic
def add_action_evidence(
    *,
    actor: User,
    action: CorrectiveAction,
    file_asset: FileAsset,
    description: str,
) -> ActionEvidence:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    locked = CorrectiveAction.objects.select_for_update().get(pk=action.pk)
    if locked.owner_id != actor.pk:
        raise PermissionDenied("Solo el responsable ejecutor adjunta evidencia.")
    if locked.status not in {
        CorrectiveActionStatus.IN_PROGRESS,
        CorrectiveActionStatus.REOPENED,
    }:
        raise ValidationError("La evidencia requiere una acción en ejecución o reabierta.")
    if file_asset.scan_status != ScanStatus.CLEAN or not file_asset.synthetic_confirmed:
        raise ValidationError("La evidencia debe ser sintética y estar validada.")
    link = ActionEvidence(
        action=locked,
        file_asset=file_asset,
        description=description,
        created_by=actor,
        updated_by=actor,
    )
    link.full_clean()
    link.save()
    record_event(
        actor=actor,
        object_type="improvements.ActionEvidence",
        object_id=link.pk,
        action="corrective_action.evidence_added",
        result=EventResult.SUCCESS,
        context={"action_id": str(locked.pk), "file_hash": file_asset.sha256},
    )
    return link


@transaction.atomic
def submit_action_verification(
    *, actor: User, action: CorrectiveAction
) -> CorrectiveAction:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    locked = (
        CorrectiveAction.objects.select_for_update()
        .select_related("finding", "owner")
        .get(pk=action.pk)
    )
    if locked.owner_id != actor.pk:
        raise PermissionDenied("Solo el responsable puede terminar la ejecución.")
    if locked.status != CorrectiveActionStatus.IN_PROGRESS:
        raise ValidationError("Solo una acción en ejecución pasa a verificación.")
    if not locked.owner.is_active:
        raise ValidationError("RN-017: reasigne al responsable inactivo antes de continuar.")
    if not locked.evidence.exists():
        raise ValidationError("La verificación requiere evidencia sintética.")
    locked.status = CorrectiveActionStatus.IN_VERIFICATION
    locked.completed_at = timezone.now()
    locked.completed_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "completed_at",
            "completed_by",
            "updated_by",
            "updated_at",
        ]
    )
    _set_finding_status(
        finding=locked.finding, status=FindingStatus.IN_VERIFICATION, actor=actor
    )
    return locked


def _all_mandatory_actions_effective(*, finding: Finding) -> bool:
    actions = list(
        CorrectiveAction.objects.filter(finding=finding, is_mandatory=True).exclude(
            status=CorrectiveActionStatus.CANCELLED
        )
    )
    return bool(actions) and all(
        action.status == CorrectiveActionStatus.CLOSED
        and action.effectiveness_reviews.filter(
            result=EffectivenessResult.EFFECTIVE
        ).exists()
        for action in actions
    )


@transaction.atomic
def review_action_effectiveness(
    *,
    actor: User,
    action: CorrectiveAction,
    result: EffectivenessResult,
    notes: str,
) -> EffectivenessReview:
    _require(actor, Capability.APPROVE_IMPROVEMENTS)
    normalized_notes = notes.strip()
    if not normalized_notes:
        raise ValidationError("La revisión de eficacia requiere notas.")
    locked = (
        CorrectiveAction.objects.select_for_update()
        .select_related("finding")
        .get(pk=action.pk)
    )
    if locked.status != CorrectiveActionStatus.IN_VERIFICATION:
        raise ValidationError("Solo una acción en verificación admite evaluar eficacia.")
    if actor.pk in {locked.owner_id, locked.completed_by_id}:
        raise PermissionDenied("RN-018: el responsable no aprueba su propia eficacia.")
    if not locked.evidence.exists():
        raise ValidationError("La eficacia no puede revisarse sin evidencia.")
    now = timezone.now()
    reopens = result == EffectivenessResult.INEFFECTIVE
    review = EffectivenessReview(
        action=locked,
        reviewer=actor,
        reviewed_at=now,
        result=result,
        notes=normalized_notes,
        reopens_action=reopens,
        created_by=actor,
        updated_by=actor,
    )
    review.full_clean()
    review.save()
    locked.status = (
        CorrectiveActionStatus.REOPENED if reopens else CorrectiveActionStatus.CLOSED
    )
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "updated_by", "updated_at"])
    finding = Finding.objects.select_for_update().get(pk=locked.finding_id)
    if reopens:
        _set_finding_status(
            finding=finding, status=FindingStatus.REOPENED, actor=actor
        )
    elif _all_mandatory_actions_effective(finding=finding):
        _set_finding_status(finding=finding, status=FindingStatus.CLOSED, actor=actor)
    elif CorrectiveAction.objects.filter(
        finding=finding, status=CorrectiveActionStatus.IN_VERIFICATION
    ).exists():
        _set_finding_status(
            finding=finding, status=FindingStatus.IN_VERIFICATION, actor=actor
        )
    else:
        _set_finding_status(
            finding=finding, status=FindingStatus.WITH_PLAN, actor=actor
        )
    record_event(
        actor=actor,
        object_type="improvements.EffectivenessReview",
        object_id=review.pk,
        action="corrective_action.effectiveness_reviewed",
        result=EventResult.SUCCESS,
        reason=normalized_notes,
        context={
            "action_id": str(locked.pk),
            "finding_status": finding.status,
            "result": review.result,
        },
    )
    return review


@transaction.atomic
def restart_reopened_action(
    *, actor: User, action: CorrectiveAction, reason: str
) -> CorrectiveAction:
    _require(actor, Capability.MANAGE_IMPROVEMENTS)
    normalized = _require_reason(reason)
    locked = CorrectiveAction.objects.select_for_update().select_related("owner").get(
        pk=action.pk
    )
    if locked.owner_id != actor.pk:
        raise PermissionDenied("Solo el responsable puede reiniciar la acción.")
    if locked.status != CorrectiveActionStatus.REOPENED:
        raise ValidationError("Solo una acción no eficaz puede reiniciarse.")
    if not locked.owner.is_active:
        raise ValidationError("RN-017: reasigne al responsable inactivo.")
    locked.status = CorrectiveActionStatus.IN_PROGRESS
    locked.completed_at = None
    locked.completed_by = None
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "completed_at",
            "completed_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="improvements.CorrectiveAction",
        object_id=locked.pk,
        action="corrective_action.restarted",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={},
    )
    return locked
