from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import capability_required
from apps.accounts.policies import Capability

from .models import Indicator
from .selectors import indicator_catalog, indicator_detail


@capability_required(Capability.VIEW_REPORTS)
def catalog(request: HttpRequest) -> HttpResponse:
    return render(request, "indicators/catalog.html", {"indicators": indicator_catalog()})


@capability_required(Capability.VIEW_REPORTS)
def detail(request: HttpRequest, indicator_id: UUID) -> HttpResponse:
    try:
        indicator = indicator_detail(indicator_id=indicator_id)
    except (Indicator.DoesNotExist, ValueError) as exc:
        raise Http404("Indicador no encontrado.") from exc
    return render(request, "indicators/detail.html", {"indicator": indicator})
