from __future__ import annotations

from datetime import date
from uuid import UUID

from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.accounts.decorators import capability_required
from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability

from .models import AnalysisDefinition, AnalysisRun, DefinitionStatus
from .presentation import analysis_presentation, control_chart_presentation
from .selectors import analysis_catalog, analysis_run_detail, recent_analysis_runs
from .services import run_analysis


def _date(value: str, field: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError({field: "La fecha debe usar formato AAAA-MM-DD."}) from exc


@capability_required(Capability.VIEW_ANALYTICS)
def catalog(request: HttpRequest) -> HttpResponse:
    user = request.user
    return render(
        request,
        "analytics/catalog.html",
        {
            "can_run": isinstance(user, User) and has_capability(user, Capability.RUN_ANALYTICS),
            "definitions": analysis_catalog(),
            "recent_runs": recent_analysis_runs(),
        },
    )


@capability_required(Capability.RUN_ANALYTICS)
def execute(request: HttpRequest, definition_id: UUID) -> HttpResponse:
    if request.method != "POST":
        raise Http404("La ejecución analítica requiere una solicitud POST.")
    try:
        definition = AnalysisDefinition.objects.get(
            pk=definition_id, status=DefinitionStatus.PUBLISHED
        )
    except AnalysisDefinition.DoesNotExist as exc:
        raise Http404("Definición analítica no encontrada.") from exc
    actor = request.user
    if not isinstance(actor, User):
        raise Http404("Usuario no encontrado.")
    try:
        run = run_analysis(
            actor=actor,
            definition=definition,
            period_start=_date(str(request.POST.get("period_start", "")), "period_start"),
            period_end=_date(str(request.POST.get("period_end", "")), "period_end"),
        )
    except ValidationError as exc:
        return HttpResponse("; ".join(exc.messages), status=400)
    return redirect("analytics:run-detail", run_id=run.pk)


@capability_required(Capability.VIEW_ANALYTICS)
def run_detail(request: HttpRequest, run_id: UUID) -> HttpResponse:
    try:
        run = analysis_run_detail(run_id=run_id)
    except AnalysisRun.DoesNotExist as exc:
        raise Http404("Ejecución analítica no encontrada.") from exc
    return render(
        request,
        "analytics/run_detail.html",
        {
            "run": run,
            "analysis": analysis_presentation(run),
            "control_chart": control_chart_presentation(run),
        },
    )
