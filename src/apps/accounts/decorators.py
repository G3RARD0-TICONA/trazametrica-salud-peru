from collections.abc import Callable
from functools import wraps
from typing import Any, cast
from uuid import UUID

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
                from apps.auditlog.models import EventResult
                from apps.auditlog.services import record_event

                correlation_id = getattr(request, "correlation_id", None)
                record_event(
                    actor=user,
                    object_type="authorization",
                    object_id=None,
                    action="capability.denied",
                    result=EventResult.DENIED,
                    reason=f"Capacidad requerida: {capability}",
                    context={"method": request.method, "path": request.path},
                    correlation_id=(correlation_id if isinstance(correlation_id, UUID) else None),
                )
                raise PermissionDenied("No cuenta con la capacidad requerida.")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
