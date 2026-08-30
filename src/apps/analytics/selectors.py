from __future__ import annotations

from uuid import UUID

from django.db.models import Prefetch, QuerySet

from .models import AnalysisDefinition, AnalysisRun, DefinitionStatus


def analysis_catalog() -> QuerySet[AnalysisDefinition]:
    runs = AnalysisRun.objects.select_related("requested_by").order_by("-executed_at")
    return (
        AnalysisDefinition.objects.filter(status=DefinitionStatus.PUBLISHED)
        .select_related("target_indicator", "published_by")
        .prefetch_related(Prefetch("runs", queryset=runs, to_attr="ordered_runs"))
        .order_by("analysis_type", "code")
    )


def analysis_run_detail(*, run_id: UUID) -> AnalysisRun:
    return AnalysisRun.objects.select_related("definition__target_indicator", "requested_by").get(
        pk=run_id
    )


def recent_analysis_runs(*, limit: int = 30) -> QuerySet[AnalysisRun]:
    return AnalysisRun.objects.select_related(
        "definition__target_indicator", "requested_by"
    ).order_by("-executed_at")[:limit]
