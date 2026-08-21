from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import capability_required
from apps.accounts.policies import Capability
from apps.audits.models import Finding

from .selectors import (
    corrective_action_alert_status,
    corrective_action_catalog,
    finding_improvement_catalog,
    finding_improvement_detail,
)


@capability_required(Capability.VIEW_REPORTS)
def catalog(request: HttpRequest) -> HttpResponse:
    actions = [
        (action, corrective_action_alert_status(action=action))
        for action in corrective_action_catalog()
    ]
    return render(
        request,
        "improvements/catalog.html",
        {"actions": actions, "findings": finding_improvement_catalog()},
    )


@capability_required(Capability.VIEW_REPORTS)
def detail(request: HttpRequest, finding_id: UUID) -> HttpResponse:
    try:
        finding = finding_improvement_detail(finding_id=finding_id)
    except (Finding.DoesNotExist, ValueError) as exc:
        raise Http404("Hallazgo no encontrado.") from exc
    return render(request, "improvements/detail.html", {"finding": finding})
