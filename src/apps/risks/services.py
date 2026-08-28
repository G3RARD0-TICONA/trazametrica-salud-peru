from __future__ import annotations

from datetime import date, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.auditlog.models import EventResult
from apps.auditlog.services import record_event
from apps.audits.models import Finding
from apps.improvements.models import CorrectiveAction
from apps.indicators.models import Indicator
from apps.organizations.models import Organization
from apps.processes.models import Process

from .models import (
    AssessmentStatus,
    Control,
    ControlFrequency,
    ControlReview,
    ControlReviewResult,
    ControlType,
    ControlVersion,
    ControlVersionStatus,
    ExpectedEffectiveness,
    Risk,
    RiskActionLink,
    RiskAssessment,
    RiskControl,
    RiskFindingLink,
    RiskIndicatorLink,
    RiskLevel,
    RiskStatus,
    risk_level_for,
)


def _require(actor: User, capability: Capability) -> None:
    if not actor.is_active or not has_capability(actor, capability):
        raise PermissionDenied("El actor no cuenta con la capacidad de riesgos requerida.")


def _reason(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValidationError("La decisión requiere un motivo.")
    return normalized


def _risk_status_from_assessment(assessment: RiskAssessment) -> RiskStatus:
    if assessment.residual_level is not None:
        if assessment.residual_band in {RiskLevel.LOW, RiskLevel.MEDIUM}:
            return RiskStatus.CONTROLLED
        return RiskStatus.UNDER_TREATMENT
    if assessment.inherent_band in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        return RiskStatus.UNDER_TREATMENT
    return RiskStatus.ASSESSED


@transaction.atomic
def create_risk(
    *,
    actor: User,
    organization: Organization,
    process: Process,
    code: str,
    cause: str,
    event: str,
    consequence: str,
    owner: User,
) -> Risk:
    _require(actor, Capability.MANAGE_RISKS)
    if not organization.is_active or not process.is_active:
        raise ValidationError("La organización y el proceso deben estar activos.")
    if process.organization_id != organization.pk:
        raise ValidationError("El proceso debe pertenecer a la organización del riesgo.")
    if not owner.is_active:
        raise ValidationError("El riesgo requiere un responsable activo.")
    risk = Risk(
        organization=organization,
        process=process,
        code=code,
        cause=cause,
        event=event,
        consequence=consequence,
        owner=owner,
        status=RiskStatus.IDENTIFIED,
        created_by=actor,
        updated_by=actor,
    )
    risk.full_clean()
    risk.save()
    record_event(
        actor=actor,
        object_type="risks.Risk",
        object_id=risk.pk,
        action="risk.created",
        result=EventResult.SUCCESS,
        context={"organization_id": str(organization.pk), "process_id": str(process.pk)},
    )
    return risk


@transaction.atomic
def create_risk_assessment(
    *,
    actor: User,
    risk: Risk,
    probability: int,
    impact: int,
    next_review_date: date,
    residual_probability: int | None = None,
    residual_impact: int | None = None,
) -> RiskAssessment:
    _require(actor, Capability.MANAGE_RISKS)
    locked_risk = Risk.objects.select_for_update().select_related("owner").get(pk=risk.pk)
    if locked_risk.status == RiskStatus.CLOSED:
        raise ValidationError("Un riesgo cerrado debe reabrirse antes de reevaluarse.")
    if not locked_risk.owner.is_active:
        raise ValidationError("Reasigne al responsable inactivo antes de evaluar.")
    if next_review_date <= timezone.localdate():
        raise ValidationError("La próxima revisión debe ser futura.")
    if (residual_probability is None) != (residual_impact is None):
        raise ValidationError("La probabilidad y el impacto residual deben informarse juntos.")
    inherent = probability * impact
    residual = (
        residual_probability * residual_impact
        if residual_probability is not None and residual_impact is not None
        else None
    )
    last_version = (
        RiskAssessment.objects.filter(risk=locked_risk)
        .order_by("-version_no")
        .values_list("version_no", flat=True)
        .first()
    )
    assessment = RiskAssessment(
        risk=locked_risk,
        version_no=(last_version or 0) + 1,
        status=AssessmentStatus.DRAFT,
        probability=probability,
        impact=impact,
        inherent_level=inherent,
        inherent_band=risk_level_for(inherent),
        residual_probability=residual_probability,
        residual_impact=residual_impact,
        residual_level=residual,
        residual_band=risk_level_for(residual) if residual is not None else "",
        assessed_at=timezone.now(),
        next_review_date=next_review_date,
        created_by=actor,
        updated_by=actor,
    )
    assessment.full_clean()
    assessment.save()
    record_event(
        actor=actor,
        object_type="risks.RiskAssessment",
        object_id=assessment.pk,
        action="risk.assessment_created",
        result=EventResult.SUCCESS,
        context={
            "inherent_level": inherent,
            "residual_level": residual,
            "risk_id": str(locked_risk.pk),
            "version_no": assessment.version_no,
        },
    )
    return assessment


@transaction.atomic
def submit_risk_assessment(*, actor: User, assessment: RiskAssessment) -> RiskAssessment:
    _require(actor, Capability.MANAGE_RISKS)
    locked = RiskAssessment.objects.select_for_update().get(pk=assessment.pk)
    if locked.status != AssessmentStatus.DRAFT:
        raise ValidationError("Solo una evaluación en borrador puede enviarse.")
    if RiskAssessment.objects.filter(
        risk=locked.risk, status=AssessmentStatus.IN_REVIEW
    ).exclude(pk=locked.pk).exists():
        raise ValidationError("El riesgo ya tiene otra evaluación en revisión.")
    locked.status = AssessmentStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "submitted_at", "submitted_by", "updated_by", "updated_at"]
    )
    record_event(
        actor=actor,
        object_type="risks.RiskAssessment",
        object_id=locked.pk,
        action="risk.assessment_submitted",
        result=EventResult.SUCCESS,
        context={"risk_id": str(locked.risk_id)},
    )
    return locked


@transaction.atomic
def reject_risk_assessment(
    *, actor: User, assessment: RiskAssessment, reason: str
) -> RiskAssessment:
    _require(actor, Capability.APPROVE_RISKS)
    normalized = _reason(reason)
    locked = RiskAssessment.objects.select_for_update().get(pk=assessment.pk)
    if locked.status != AssessmentStatus.IN_REVIEW:
        raise ValidationError("Solo una evaluación en revisión puede rechazarse.")
    if actor.pk in {locked.created_by_id, locked.submitted_by_id}:
        raise PermissionDenied("El autor no puede decidir su propia evaluación.")
    locked.status = AssessmentStatus.DRAFT
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "decision_reason", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="risks.RiskAssessment",
        object_id=locked.pk,
        action="risk.assessment_rejected",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"risk_id": str(locked.risk_id)},
    )
    return locked


@transaction.atomic
def approve_risk_assessment(
    *, actor: User, assessment: RiskAssessment, reason: str
) -> RiskAssessment:
    _require(actor, Capability.APPROVE_RISKS)
    normalized = _reason(reason)
    locked = RiskAssessment.objects.select_for_update().select_related("risk").get(
        pk=assessment.pk
    )
    if locked.status != AssessmentStatus.IN_REVIEW:
        raise ValidationError("Solo una evaluación en revisión puede aprobarse.")
    if actor.pk in {locked.created_by_id, locked.submitted_by_id}:
        raise PermissionDenied("El autor no puede aprobar su propia evaluación.")
    now = timezone.now()
    prior = RiskAssessment.objects.select_for_update().filter(
        risk=locked.risk, status=AssessmentStatus.APPROVED
    )
    for item in prior:
        item.status = AssessmentStatus.SUPERSEDED
        item.updated_by = actor
        item.full_clean()
        item.save(update_fields=["status", "updated_by", "updated_at"])
    locked.status = AssessmentStatus.APPROVED
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
    risk = Risk.objects.select_for_update().get(pk=locked.risk_id)
    risk.status = _risk_status_from_assessment(locked)
    risk.updated_by = actor
    risk.full_clean()
    risk.save(update_fields=["status", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="risks.RiskAssessment",
        object_id=locked.pk,
        action="risk.assessment_approved",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"risk_id": str(risk.pk), "risk_status": risk.status},
    )
    return locked


@transaction.atomic
def create_control(
    *, actor: User, organization: Organization, code: str, name: str, owner: User
) -> Control:
    _require(actor, Capability.MANAGE_RISKS)
    if not organization.is_active or not owner.is_active:
        raise ValidationError("La organización y el responsable deben estar activos.")
    control = Control(
        organization=organization,
        code=code,
        name=name,
        owner=owner,
        created_by=actor,
        updated_by=actor,
    )
    control.full_clean()
    control.save()
    record_event(
        actor=actor,
        object_type="risks.Control",
        object_id=control.pk,
        action="control.created",
        result=EventResult.SUCCESS,
        context={"organization_id": str(organization.pk)},
    )
    return control


@transaction.atomic
def create_control_version(
    *,
    actor: User,
    control: Control,
    description: str,
    control_type: ControlType,
    frequency: ControlFrequency,
) -> ControlVersion:
    _require(actor, Capability.MANAGE_RISKS)
    locked = Control.objects.select_for_update().select_related("owner").get(pk=control.pk)
    if not locked.is_active or not locked.owner.is_active:
        raise ValidationError("El control y su responsable deben estar activos.")
    last_version = (
        ControlVersion.objects.filter(control=locked)
        .order_by("-version_no")
        .values_list("version_no", flat=True)
        .first()
    )
    version = ControlVersion(
        control=locked,
        version_no=(last_version or 0) + 1,
        description=description,
        control_type=control_type,
        frequency=frequency,
        created_by=actor,
        updated_by=actor,
    )
    version.full_clean()
    version.save()
    record_event(
        actor=actor,
        object_type="risks.ControlVersion",
        object_id=version.pk,
        action="control.version_created",
        result=EventResult.SUCCESS,
        context={"control_id": str(locked.pk), "version_no": version.version_no},
    )
    return version


@transaction.atomic
def submit_control_version(*, actor: User, version: ControlVersion) -> ControlVersion:
    _require(actor, Capability.MANAGE_RISKS)
    locked = ControlVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != ControlVersionStatus.DRAFT:
        raise ValidationError("Solo una versión en borrador puede enviarse.")
    locked.status = ControlVersionStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "submitted_at", "submitted_by", "updated_by", "updated_at"]
    )
    record_event(
        actor=actor,
        object_type="risks.ControlVersion",
        object_id=locked.pk,
        action="control.version_submitted",
        result=EventResult.SUCCESS,
        context={"control_id": str(locked.control_id)},
    )
    return locked


@transaction.atomic
def approve_control_version(
    *, actor: User, version: ControlVersion, valid_from: date, reason: str
) -> ControlVersion:
    _require(actor, Capability.APPROVE_RISKS)
    normalized = _reason(reason)
    locked = ControlVersion.objects.select_for_update().select_related("control").get(
        pk=version.pk
    )
    if locked.status != ControlVersionStatus.IN_REVIEW:
        raise ValidationError("Solo una versión en revisión puede aprobarse.")
    if actor.pk in {locked.created_by_id, locked.submitted_by_id}:
        raise PermissionDenied("El autor no puede aprobar su propio control.")
    prior = ControlVersion.objects.select_for_update().filter(
        control=locked.control, status=ControlVersionStatus.EFFECTIVE
    )
    for item in prior:
        if item.valid_from is None or valid_from <= item.valid_from:
            raise ValidationError("La nueva vigencia debe iniciar después de la anterior.")
        item.status = ControlVersionStatus.SUPERSEDED
        item.valid_to = valid_from - timedelta(days=1)
        item.updated_by = actor
        item.full_clean()
        item.save(update_fields=["status", "valid_to", "updated_by", "updated_at"])
    locked.status = ControlVersionStatus.EFFECTIVE
    locked.valid_from = valid_from
    locked.approved_at = timezone.now()
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
        object_type="risks.ControlVersion",
        object_id=locked.pk,
        action="control.version_approved",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"control_id": str(locked.control_id), "version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def link_risk_control(
    *,
    actor: User,
    risk: Risk,
    control_version: ControlVersion,
    valid_from: date,
    effectiveness_expected: ExpectedEffectiveness,
) -> RiskControl:
    _require(actor, Capability.MANAGE_RISKS)
    locked_risk = Risk.objects.select_for_update().get(pk=risk.pk)
    version = ControlVersion.objects.select_related("control").get(pk=control_version.pk)
    link = RiskControl(
        risk=locked_risk,
        control_version=version,
        valid_from=valid_from,
        effectiveness_expected=effectiveness_expected,
        created_by=actor,
        updated_by=actor,
    )
    link.full_clean()
    link.save()
    if locked_risk.status in {RiskStatus.ASSESSED, RiskStatus.REOPENED}:
        locked_risk.status = RiskStatus.UNDER_TREATMENT
        locked_risk.updated_by = actor
        locked_risk.full_clean()
        locked_risk.save(update_fields=["status", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="risks.RiskControl",
        object_id=link.pk,
        action="risk.control_linked",
        result=EventResult.SUCCESS,
        context={
            "control_version_id": str(version.pk),
            "risk_id": str(locked_risk.pk),
        },
    )
    return link


@transaction.atomic
def review_control(
    *,
    actor: User,
    risk_control: RiskControl,
    result: ControlReviewResult,
    notes: str,
    next_review_date: date,
) -> ControlReview:
    _require(actor, Capability.REVIEW_RISKS)
    normalized = notes.strip()
    if not normalized:
        raise ValidationError("La revisión requiere notas.")
    locked = (
        RiskControl.objects.select_for_update()
        .select_related("risk__owner", "control_version__control__owner")
        .get(pk=risk_control.pk)
    )
    if actor.pk in {locked.risk.owner_id, locked.control_version.control.owner_id}:
        raise PermissionDenied("El responsable no revisa su propio riesgo o control.")
    review = ControlReview(
        risk_control=locked,
        reviewer=actor,
        reviewed_at=timezone.now(),
        result=result,
        notes=normalized,
        next_review_date=next_review_date,
        created_by=actor,
        updated_by=actor,
    )
    review.full_clean()
    review.save()
    record_event(
        actor=actor,
        object_type="risks.ControlReview",
        object_id=review.pk,
        action="control.reviewed",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"risk_control_id": str(locked.pk), "result": review.result},
    )
    return review


def _validate_link_scope(risk: Risk, organization_id: object) -> None:
    if risk.organization_id != organization_id:
        raise ValidationError("El objeto vinculado debe pertenecer a la organización del riesgo.")


@transaction.atomic
def link_risk_indicator(
    *, actor: User, risk: Risk, indicator: Indicator
) -> RiskIndicatorLink:
    _require(actor, Capability.MANAGE_RISKS)
    _validate_link_scope(risk, indicator.organization_id)
    link = RiskIndicatorLink(
        risk=risk, indicator=indicator, created_by=actor, updated_by=actor
    )
    link.full_clean()
    link.save()
    record_event(
        actor=actor,
        object_type="risks.RiskIndicatorLink",
        object_id=link.pk,
        action="risk.indicator_linked",
        result=EventResult.SUCCESS,
        context={"indicator_id": str(indicator.pk), "risk_id": str(risk.pk)},
    )
    return link


@transaction.atomic
def link_risk_finding(*, actor: User, risk: Risk, finding: Finding) -> RiskFindingLink:
    _require(actor, Capability.MANAGE_RISKS)
    _validate_link_scope(risk, finding.execution.audit_plan.organization_id)
    link = RiskFindingLink(risk=risk, finding=finding, created_by=actor, updated_by=actor)
    link.full_clean()
    link.save()
    record_event(
        actor=actor,
        object_type="risks.RiskFindingLink",
        object_id=link.pk,
        action="risk.finding_linked",
        result=EventResult.SUCCESS,
        context={"finding_id": str(finding.pk), "risk_id": str(risk.pk)},
    )
    return link


@transaction.atomic
def link_risk_action(
    *, actor: User, risk: Risk, action: CorrectiveAction
) -> RiskActionLink:
    _require(actor, Capability.MANAGE_RISKS)
    _validate_link_scope(risk, action.finding.execution.audit_plan.organization_id)
    link = RiskActionLink(risk=risk, action=action, created_by=actor, updated_by=actor)
    link.full_clean()
    link.save()
    record_event(
        actor=actor,
        object_type="risks.RiskActionLink",
        object_id=link.pk,
        action="risk.action_linked",
        result=EventResult.SUCCESS,
        context={"action_id": str(action.pk), "risk_id": str(risk.pk)},
    )
    return link


def _approved_assessment(risk: Risk) -> RiskAssessment:
    try:
        return RiskAssessment.objects.get(risk=risk, status=AssessmentStatus.APPROVED)
    except RiskAssessment.DoesNotExist as exc:
        raise ValidationError("El riesgo requiere una evaluación residual aprobada.") from exc


def _controls_current(risk: Risk, on_date: date) -> bool:
    links = list(
        RiskControl.objects.filter(risk=risk, valid_from__lte=on_date)
        .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=on_date))
        .select_related("control_version__control")
    )
    if not links:
        return False
    for link in links:
        version = link.control_version
        control = version.control
        review = link.reviews.order_by("-reviewed_at").first()
        version_applies = version.status == ControlVersionStatus.EFFECTIVE or (
            version.status == ControlVersionStatus.SUPERSEDED
            and version.valid_to is not None
            and version.valid_to >= on_date
        )
        if (
            not control.is_active
            or not control.owner.is_active
            or not version_applies
            or version.valid_from is None
            or version.valid_from > on_date
            or (version.valid_to is not None and version.valid_to < on_date)
            or review is None
            or review.next_review_date < on_date
            or review.result == ControlReviewResult.INEFFECTIVE
        ):
            return False
    return True


@transaction.atomic
def accept_residual_risk(*, actor: User, risk: Risk, reason: str) -> Risk:
    _require(actor, Capability.APPROVE_RISKS)
    normalized = _reason(reason)
    locked = Risk.objects.select_for_update().get(pk=risk.pk)
    assessment = _approved_assessment(locked)
    if assessment.residual_level is None:
        raise ValidationError("La aceptación requiere evaluación residual.")
    if assessment.residual_band in {RiskLevel.HIGH, RiskLevel.CRITICAL} and not _controls_current(
        locked, timezone.localdate()
    ):
        raise ValidationError("RN-026: el riesgo alto o crítico requiere controles vigentes.")
    if actor.pk in {locked.owner_id, assessment.created_by_id, assessment.submitted_by_id}:
        raise PermissionDenied("La aceptación residual requiere decisión independiente.")
    locked.status = RiskStatus.ACCEPTED
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "decision_reason", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="risks.Risk",
        object_id=locked.pk,
        action="risk.residual_accepted",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"residual_band": assessment.residual_band},
    )
    return locked


@transaction.atomic
def close_risk(*, actor: User, risk: Risk, reason: str) -> Risk:
    _require(actor, Capability.APPROVE_RISKS)
    normalized = _reason(reason)
    locked = Risk.objects.select_for_update().get(pk=risk.pk)
    assessment = _approved_assessment(locked)
    if assessment.residual_level is None:
        raise ValidationError("RN-026: el cierre requiere evaluación residual.")
    if assessment.residual_band in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        raise ValidationError("El riesgo residual alto o crítico no puede cerrarse.")
    if not _controls_current(locked, timezone.localdate()):
        raise ValidationError("RN-026: el cierre requiere controles revisados y vigentes.")
    if actor.pk in {locked.owner_id, assessment.created_by_id, assessment.submitted_by_id}:
        raise PermissionDenied("El cierre requiere decisión independiente.")
    locked.status = RiskStatus.CLOSED
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "decision_reason", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="risks.Risk",
        object_id=locked.pk,
        action="risk.closed",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={"residual_level": assessment.residual_level},
    )
    return locked


@transaction.atomic
def reopen_risk(*, actor: User, risk: Risk, reason: str) -> Risk:
    _require(actor, Capability.MANAGE_RISKS)
    normalized = _reason(reason)
    locked = Risk.objects.select_for_update().get(pk=risk.pk)
    if locked.status not in {RiskStatus.ACCEPTED, RiskStatus.CLOSED, RiskStatus.CONTROLLED}:
        raise ValidationError("Solo un riesgo aceptado, controlado o cerrado puede reabrirse.")
    locked.status = RiskStatus.REOPENED
    locked.decision_reason = normalized
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "decision_reason", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="risks.Risk",
        object_id=locked.pk,
        action="risk.reopened",
        result=EventResult.SUCCESS,
        reason=normalized,
        context={},
    )
    return locked
