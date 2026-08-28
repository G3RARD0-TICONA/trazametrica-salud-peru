from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from django.db.models import Prefetch, Q, QuerySet
from django.utils import timezone

from .models import (
    AssessmentStatus,
    ControlReview,
    ControlReviewResult,
    ControlVersionStatus,
    Risk,
    RiskAssessment,
    RiskControl,
    RiskLevel,
    RiskStatus,
)


def risk_catalog() -> QuerySet[Risk]:
    approved_assessments = RiskAssessment.objects.filter(
        status=AssessmentStatus.APPROVED
    ).order_by("-version_no")
    controls = RiskControl.objects.select_related("control_version__control").order_by(
        "control_version__control__code"
    )
    return (
        Risk.objects.select_related("organization", "process", "owner")
        .prefetch_related(
            Prefetch(
                "assessments",
                queryset=approved_assessments,
                to_attr="approved_assessments",
            ),
            Prefetch("risk_controls", queryset=controls, to_attr="ordered_controls"),
        )
        .order_by("code")
    )


def risk_detail(*, risk_id: UUID) -> Risk:
    reviews = ControlReview.objects.select_related("reviewer").order_by("-reviewed_at")
    controls = (
        RiskControl.objects.select_related("control_version__control")
        .prefetch_related(Prefetch("reviews", queryset=reviews, to_attr="ordered_reviews"))
        .order_by("control_version__control__code")
    )
    return (
        Risk.objects.select_related("organization", "process", "owner")
        .prefetch_related(
            "assessments__approved_by",
            Prefetch("risk_controls", queryset=controls, to_attr="ordered_controls"),
            "indicator_links__indicator",
            "finding_links__finding",
            "action_links__action",
        )
        .get(pk=risk_id)
    )


def risk_alert_status(*, risk: Risk, on_date: date | None = None) -> str:
    current = on_date or timezone.localdate()
    if risk.status == RiskStatus.CLOSED:
        return "not_applicable"
    if not risk.owner.is_active:
        return "unassigned"
    assessment = risk.assessments.filter(status=AssessmentStatus.APPROVED).order_by(
        "-version_no"
    ).first()
    if assessment is None:
        return "pending_assessment"
    if assessment.next_review_date < current:
        return "overdue"
    if assessment.next_review_date <= current + timedelta(days=7):
        return "upcoming"
    score_band = assessment.residual_band or assessment.inherent_band
    if score_band in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        current_controls = (
            risk.risk_controls.filter(
                valid_from__lte=current,
                control_version__status__in=(
                    ControlVersionStatus.EFFECTIVE,
                    ControlVersionStatus.SUPERSEDED,
                ),
                control_version__valid_from__lte=current,
                control_version__control__is_active=True,
                control_version__control__owner__is_active=True,
            )
            .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=current))
            .filter(
                Q(control_version__valid_to__isnull=True)
                | Q(control_version__valid_to__gte=current)
            )
        )
        if not current_controls.exists():
            return "treatment_required"
    return "on_time"


def control_alert_status(*, link: RiskControl, on_date: date | None = None) -> str:
    current = on_date or timezone.localdate()
    control = link.control_version.control
    version_applies = link.control_version.status == ControlVersionStatus.EFFECTIVE or (
        link.control_version.status == ControlVersionStatus.SUPERSEDED
        and link.control_version.valid_to is not None
        and link.control_version.valid_to >= current
    )
    if link.valid_to is not None and link.valid_to < current:
        return "not_applicable"
    if (
        not version_applies
        or link.control_version.valid_from is None
        or link.control_version.valid_from > current
        or (
            link.control_version.valid_to is not None
            and link.control_version.valid_to < current
        )
    ):
        return "not_applicable"
    if not control.is_active or not control.owner.is_active:
        return "unassigned"
    review = link.reviews.order_by("-reviewed_at").first()
    if review is None:
        return "pending_review"
    if review.result == ControlReviewResult.INEFFECTIVE:
        return "ineffective"
    if review.next_review_date < current:
        return "overdue"
    if review.next_review_date <= current + timedelta(days=7):
        return "upcoming"
    return "on_time"
