from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import capability_required
from apps.accounts.policies import Capability

from .selectors import document_catalog, reference_catalog


@capability_required(Capability.VIEW_DOCUMENTS)
def catalog(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "documents/catalog.html",
        {
            "documents": document_catalog(),
            "references": reference_catalog(),
        },
    )
