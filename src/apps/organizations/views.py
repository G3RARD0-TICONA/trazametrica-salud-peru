from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import capability_required
from apps.accounts.policies import Capability

from .selectors import active_organization_structure


@capability_required(Capability.VIEW_ORGANIZATION)
def structure(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "organizations/structure.html",
        {"organization": active_organization_structure()},
    )
