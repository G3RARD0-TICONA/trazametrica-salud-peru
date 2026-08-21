from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import capability_required
from apps.accounts.policies import Capability

from .models import AuditPlan
from .selectors import audit_plan_catalog, audit_plan_detail, finding_alert_status, finding_catalog


@capability_required(Capability.VIEW_REPORTS)
def catalog(request: HttpRequest) -> HttpResponse:
    findings = [
        (finding, finding_alert_status(finding=finding)) for finding in finding_catalog()
    ]
    return render(
        request,
        "audits/catalog.html",
        {"audit_plans": audit_plan_catalog(), "findings": findings},
    )


@capability_required(Capability.VIEW_REPORTS)
def detail(request: HttpRequest, plan_id: UUID) -> HttpResponse:
    try:
        plan = audit_plan_detail(plan_id=plan_id)
    except (AuditPlan.DoesNotExist, ValueError) as exc:
        raise Http404("Plan de auditoría no encontrado.") from exc
    return render(request, "audits/detail.html", {"plan": plan})
