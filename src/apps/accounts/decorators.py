from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from .models import User
from .policies import Capability, has_capability

ViewFunction = Callable[..., HttpResponse]


def capability_required(capability: Capability) -> Callable[[ViewFunction], ViewFunction]:
    def decorator(view_func: ViewFunction) -> ViewFunction:
        @login_required
        @wraps(view_func)
        def wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            user = cast(User, request.user)
            if not has_capability(user, capability):
                raise PermissionDenied("No cuenta con la capacidad requerida.")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
