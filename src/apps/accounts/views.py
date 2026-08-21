from typing import cast

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .decorators import capability_required
from .models import User
from .policies import Capability, active_role_codes, capabilities_for_user


@capability_required(Capability.VIEW_DASHBOARD)
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/home.html")


@capability_required(Capability.VIEW_DASHBOARD)
def access_profile(request: HttpRequest) -> HttpResponse:
    user = cast(User, request.user)
    return render(
        request,
        "accounts/access_profile.html",
        {
            "role_codes": sorted(active_role_codes(user)),
            "capabilities": sorted(cap.value for cap in capabilities_for_user(user)),
        },
    )
