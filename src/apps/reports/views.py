from __future__ import annotations

from uuid import UUID

from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import capability_required
from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.indicators.models import ResultStatus

from .models import ExportContract, ExportContractStatus
from .selectors import (
    ReportFilters,
    dashboard_filter_options,
    dashboard_rows,
    indicator_result_rows,
    published_contracts,
    recent_export_runs,
)
from .services import generate_export, parse_report_filters


@capability_required(Capability.VIEW_REPORTS)
def dashboard(request: HttpRequest) -> HttpResponse:
    filter_error = ""
    try:
        filters = parse_report_filters(request.GET)
    except ValidationError as exc:
        filters = ReportFilters()
        filter_error = "; ".join(exc.messages)
    user = request.user
    can_export = isinstance(user, User) and has_capability(user, Capability.EXPORT_REPORTS)
    context = {
        "can_export": can_export,
        "contracts": published_contracts(),
        "filter_error": filter_error,
        "filters": filters,
        "filter_values": filters.as_dict(),
        "indicator_rows": indicator_result_rows(filters)[:50],
        "metrics": dashboard_rows(filters),
        "recent_runs": recent_export_runs(),
        "result_statuses": ResultStatus.choices,
        **dashboard_filter_options(),
    }
    return render(request, "reports/dashboard.html", context)


@capability_required(Capability.EXPORT_REPORTS)
def export_contract(request: HttpRequest, contract_id: UUID) -> HttpResponse:
    if request.method != "POST":
        raise Http404("La exportación requiere una solicitud POST.")
    try:
        contract = ExportContract.objects.get(pk=contract_id, status=ExportContractStatus.PUBLISHED)
    except ExportContract.DoesNotExist as exc:
        raise Http404("Contrato de exportación no encontrado.") from exc
    filters = parse_report_filters(request.POST)
    actor = request.user
    if not isinstance(actor, User):
        raise Http404("Usuario no encontrado.")
    artifact = generate_export(actor=actor, contract=contract, filters=filters)
    response = HttpResponse(artifact.content, content_type=artifact.media_type)
    response["Content-Disposition"] = f'attachment; filename="{artifact.filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["X-Export-Run"] = str(artifact.run.pk)
    response["X-Export-SHA256"] = artifact.run.output_hash
    return response
