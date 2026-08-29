from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from django.db.models import Count, QuerySet

from apps.audits.models import Finding
from apps.improvements.models import CorrectiveAction
from apps.indicators.models import Indicator, IndicatorResult
from apps.organizations.models import Service, Site
from apps.processes.models import Process
from apps.risks.models import AssessmentStatus, Risk

from .models import DatasetCode, ExportContract, ExportContractStatus, ExportRun

ROW_LIMIT_SENTINEL = 10_001


@dataclass(frozen=True)
class ReportFilters:
    period_start: date | None = None
    period_end: date | None = None
    site_id: UUID | None = None
    service_id: UUID | None = None
    process_id: UUID | None = None
    indicator_id: UUID | None = None
    status: str = ""

    def as_dict(self) -> dict[str, str]:
        values = {
            "period_start": self.period_start.isoformat() if self.period_start else "",
            "period_end": self.period_end.isoformat() if self.period_end else "",
            "site_id": str(self.site_id) if self.site_id else "",
            "service_id": str(self.service_id) if self.service_id else "",
            "process_id": str(self.process_id) if self.process_id else "",
            "indicator_id": str(self.indicator_id) if self.indicator_id else "",
            "status": self.status,
        }
        return {key: value for key, value in values.items() if value}


def _decimal(value: Decimal) -> str:
    normalized = format(value, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


def _indicator_queryset(filters: ReportFilters) -> QuerySet[IndicatorResult]:
    queryset = IndicatorResult.objects.select_related(
        "indicator_version__indicator__organization",
        "indicator_version__indicator__process",
        "site",
        "service",
    )
    if filters.period_start:
        queryset = queryset.filter(period_end__gte=filters.period_start)
    if filters.period_end:
        queryset = queryset.filter(period_start__lte=filters.period_end)
    if filters.site_id:
        queryset = queryset.filter(site_id=filters.site_id)
    if filters.service_id:
        queryset = queryset.filter(service_id=filters.service_id)
    if filters.process_id:
        queryset = queryset.filter(indicator_version__indicator__process_id=filters.process_id)
    if filters.indicator_id:
        queryset = queryset.filter(indicator_version__indicator_id=filters.indicator_id)
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    return queryset.order_by(
        "indicator_version__indicator__code", "period_start", "site__code", "service__code"
    )


def indicator_result_rows(filters: ReportFilters) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for result in _indicator_queryset(filters)[:ROW_LIMIT_SENTINEL]:
        indicator = result.indicator_version.indicator
        rows.append(
            {
                "organization_code": indicator.organization.code,
                "site_code": result.site.code if result.site else "",
                "service_code": result.service.code if result.service else "",
                "process_code": indicator.process.code,
                "indicator_code": indicator.code,
                "indicator_name": indicator.name,
                "indicator_version": result.indicator_version.version_no,
                "period_start": result.period_start.isoformat(),
                "period_end": result.period_end.isoformat(),
                "value": _decimal(result.value),
                "unit": result.indicator_version.unit,
                "performance_status": result.performance_status,
                "result_status": result.status,
            }
        )
    return rows


def dashboard_rows(filters: ReportFilters) -> list[dict[str, object]]:
    queryset = _indicator_queryset(filters)
    grouped = (
        queryset.values("performance_status")
        .annotate(total=Count("id"))
        .order_by("performance_status")
    )
    rows = [
        {"metric": "indicator_results", "status": "all", "value": queryset.count()},
    ]
    rows.extend(
        {
            "metric": "performance_status",
            "status": str(item["performance_status"]),
            "value": int(item["total"]),
        }
        for item in grouped
    )
    return rows


def risk_rows(filters: ReportFilters) -> list[dict[str, object]]:
    queryset = Risk.objects.select_related("organization", "process", "owner").prefetch_related(
        "assessments"
    )
    if filters.process_id:
        queryset = queryset.filter(process_id=filters.process_id)
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    rows: list[dict[str, object]] = []
    for risk in queryset.order_by("code")[:ROW_LIMIT_SENTINEL]:
        assessment = next(
            (item for item in risk.assessments.all() if item.status == AssessmentStatus.APPROVED),
            None,
        )
        rows.append(
            {
                "organization_code": risk.organization.code,
                "process_code": risk.process.code,
                "risk_code": risk.code,
                "event": risk.event,
                "owner": risk.owner.username,
                "risk_status": risk.status,
                "inherent_level": assessment.inherent_level if assessment else "",
                "inherent_band": assessment.inherent_band if assessment else "",
                "residual_level": assessment.residual_level if assessment else "",
                "residual_band": assessment.residual_band if assessment else "",
                "next_review_date": (assessment.next_review_date.isoformat() if assessment else ""),
            }
        )
    return rows


def finding_rows(filters: ReportFilters) -> list[dict[str, object]]:
    queryset = Finding.objects.select_related(
        "execution__audit_plan__organization", "execution__audit_plan", "owner"
    )
    if filters.period_start:
        queryset = queryset.filter(created_at__date__gte=filters.period_start)
    if filters.period_end:
        queryset = queryset.filter(created_at__date__lte=filters.period_end)
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    return [
        {
            "organization_code": finding.execution.audit_plan.organization.code,
            "audit_code": finding.execution.audit_plan.code,
            "finding_code": finding.code,
            "finding_type": finding.finding_type,
            "impact": finding.impact,
            "finding_status": finding.status,
            "due_date": finding.due_date.isoformat() if finding.due_date else "",
            "owner": finding.owner.username,
        }
        for finding in queryset.order_by("code")[:ROW_LIMIT_SENTINEL]
    ]


def corrective_action_rows(filters: ReportFilters) -> list[dict[str, object]]:
    queryset = CorrectiveAction.objects.select_related(
        "finding__execution__audit_plan__organization", "finding", "owner"
    )
    if filters.period_start:
        queryset = queryset.filter(due_date__gte=filters.period_start)
    if filters.period_end:
        queryset = queryset.filter(due_date__lte=filters.period_end)
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    return [
        {
            "organization_code": action.finding.execution.audit_plan.organization.code,
            "finding_code": action.finding.code,
            "action_code": action.code,
            "action_status": action.status,
            "due_date": action.due_date.isoformat(),
            "owner": action.owner.username,
            "is_mandatory": action.is_mandatory,
        }
        for action in queryset.order_by("due_date", "code")[:ROW_LIMIT_SENTINEL]
    ]


def dataset_rows(*, dataset: str, filters: ReportFilters) -> list[dict[str, object]]:
    if dataset == DatasetCode.DASHBOARD:
        return dashboard_rows(filters)
    if dataset == DatasetCode.INDICATOR_RESULTS:
        return indicator_result_rows(filters)
    if dataset == DatasetCode.RISKS:
        return risk_rows(filters)
    if dataset == DatasetCode.FINDINGS:
        return finding_rows(filters)
    if dataset == DatasetCode.CORRECTIVE_ACTIONS:
        return corrective_action_rows(filters)
    raise ValueError("Conjunto de reporte no soportado.")


def published_contracts() -> QuerySet[ExportContract]:
    return ExportContract.objects.filter(status=ExportContractStatus.PUBLISHED).order_by(
        "dataset", "format", "code"
    )


def recent_export_runs(*, limit: int = 20) -> QuerySet[ExportRun]:
    return ExportRun.objects.select_related("contract", "requested_by", "file_asset").order_by(
        "-generated_at"
    )[:limit]


def dashboard_filter_options() -> dict[str, QuerySet]:
    return {
        "sites": Site.objects.filter(is_active=True).order_by("code"),
        "services": Service.objects.filter(is_active=True)
        .select_related("site")
        .order_by("site__code", "code"),
        "processes": Process.objects.filter(is_active=True).order_by("code"),
        "indicators": Indicator.objects.filter(is_active=True).order_by("code"),
    }
