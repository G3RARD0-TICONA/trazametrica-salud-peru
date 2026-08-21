from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from django.db.models import Prefetch, QuerySet

from .models import (
    AuditExecution,
    AuditPlan,
    AuditResponse,
    Finding,
    FindingEvidence,
    FindingStatus,
)


def audit_plan_catalog() -> QuerySet[AuditPlan]:
    executions = AuditExecution.objects.select_related("checklist_version").order_by(
        "-started_at"
    )
    return (
        AuditPlan.objects.select_related("organization", "lead_auditor", "approved_by")
        .prefetch_related(
            Prefetch("executions", queryset=executions, to_attr="ordered_executions")
        )
        .order_by("-planned_start", "code")
    )


def finding_catalog() -> QuerySet[Finding]:
    return (
        Finding.objects.exclude(status=FindingStatus.CANCELLED)
        .select_related("execution__audit_plan", "owner", "audit_response")
        .order_by("due_date", "-created_at")
    )


def audit_plan_detail(*, plan_id: UUID) -> AuditPlan:
    evidence = FindingEvidence.objects.select_related("file_asset").order_by("created_at")
    findings = (
        Finding.objects.select_related("owner", "audit_response")
        .prefetch_related(Prefetch("evidence", queryset=evidence, to_attr="ordered_evidence"))
        .order_by("code")
    )
    responses = AuditResponse.objects.select_related("checklist_item", "responded_by").order_by(
        "checklist_item__position"
    )
    executions = (
        AuditExecution.objects.select_related("checklist_version", "reviewed_by")
        .prefetch_related(
            Prefetch("responses", queryset=responses, to_attr="ordered_responses"),
            Prefetch("findings", queryset=findings, to_attr="ordered_findings"),
        )
        .order_by("-started_at")
    )
    return (
        AuditPlan.objects.select_related("organization", "lead_auditor", "approved_by")
        .prefetch_related(
            Prefetch("executions", queryset=executions, to_attr="ordered_executions")
        )
        .get(pk=plan_id)
    )


def finding_alert_status(*, finding: Finding, on_date: date | None = None) -> str:
    current = on_date or date.today()
    if finding.status == FindingStatus.CANCELLED or finding.due_date is None:
        return "not_applicable"
    if finding.due_date < current:
        return "overdue"
    if finding.due_date <= current + timedelta(days=7):
        return "upcoming"
    return "on_time"
