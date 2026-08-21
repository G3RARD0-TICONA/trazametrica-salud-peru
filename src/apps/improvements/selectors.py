from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from django.db.models import Prefetch, QuerySet
from django.utils import timezone

from apps.audits.models import Finding, FindingStatus

from .models import ActionEvidence, CorrectiveAction, CorrectiveActionStatus, EffectivenessReview


def corrective_action_catalog() -> QuerySet[CorrectiveAction]:
    return (
        CorrectiveAction.objects.select_related(
            "finding__execution__audit_plan", "owner", "root_cause", "approved_by"
        )
        .exclude(status=CorrectiveActionStatus.CANCELLED)
        .order_by("due_date", "code")
    )


def finding_improvement_catalog() -> QuerySet[Finding]:
    actions = corrective_action_catalog()
    return (
        Finding.objects.exclude(status=FindingStatus.CANCELLED)
        .select_related("execution__audit_plan", "owner", "root_cause_analysis")
        .prefetch_related(
            Prefetch("corrective_actions", queryset=actions, to_attr="ordered_actions")
        )
        .order_by("due_date", "code")
    )


def finding_improvement_detail(*, finding_id: UUID) -> Finding:
    evidence = ActionEvidence.objects.select_related("file_asset").order_by("created_at")
    reviews = EffectivenessReview.objects.select_related("reviewer").order_by("-reviewed_at")
    actions = (
        CorrectiveAction.objects.select_related("owner", "approved_by", "completed_by")
        .prefetch_related(
            Prefetch("evidence", queryset=evidence, to_attr="ordered_evidence"),
            Prefetch(
                "effectiveness_reviews", queryset=reviews, to_attr="ordered_reviews"
            ),
        )
        .order_by("due_date", "code")
    )
    return (
        Finding.objects.select_related(
            "execution__audit_plan", "owner", "root_cause_analysis__approved_by"
        )
        .prefetch_related(
            Prefetch("corrective_actions", queryset=actions, to_attr="ordered_actions")
        )
        .get(pk=finding_id)
    )


def corrective_action_alert_status(
    *, action: CorrectiveAction, on_date: date | None = None
) -> str:
    current = on_date or timezone.localdate()
    if action.status in {
        CorrectiveActionStatus.CLOSED,
        CorrectiveActionStatus.CANCELLED,
    }:
        return "not_applicable"
    if not action.owner.is_active:
        return "unassigned"
    if action.due_date < current:
        return "overdue"
    if action.due_date <= current + timedelta(days=7):
        return "upcoming"
    return "on_time"
