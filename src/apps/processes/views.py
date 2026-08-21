from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import capability_required
from apps.accounts.policies import Capability

from .models import Process
from .selectors import process_catalog, process_detail


@capability_required(Capability.VIEW_PROCESSES)
def catalog(request: HttpRequest) -> HttpResponse:
    return render(request, "processes/catalog.html", {"processes": process_catalog()})


@capability_required(Capability.VIEW_PROCESSES)
def detail(request: HttpRequest, process_id: UUID) -> HttpResponse:
    try:
        process = process_detail(process_id=process_id)
    except (Process.DoesNotExist, ValueError) as exc:
        raise Http404("Proceso no encontrado.") from exc
    return render(request, "processes/detail.html", {"process": process})
