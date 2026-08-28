from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import capability_required
from apps.accounts.policies import Capability

from .models import Risk
from .selectors import control_alert_status, risk_alert_status, risk_catalog, risk_detail


@capability_required(Capability.VIEW_REPORTS)
def catalog(request: HttpRequest) -> HttpResponse:
    risks = [(risk, risk_alert_status(risk=risk)) for risk in risk_catalog()]
    control_alerts = [
        (risk, link, control_alert_status(link=link))
        for risk, _alert in risks
        for link in getattr(risk, "ordered_controls", [])
    ]
    return render(
        request,
        "risks/catalog.html",
        {"risks": risks, "control_alerts": control_alerts},
    )


@capability_required(Capability.VIEW_REPORTS)
def detail(request: HttpRequest, risk_id: UUID) -> HttpResponse:
    try:
        risk = risk_detail(risk_id=risk_id)
    except (Risk.DoesNotExist, ValueError) as exc:
        raise Http404("Riesgo no encontrado.") from exc
    return render(request, "risks/detail.html", {"risk": risk})
