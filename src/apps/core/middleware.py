from __future__ import annotations

import logging
import uuid
from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_cache_control, patch_vary_headers

logger = logging.getLogger("trazametrica.requests")


class RequestSafetyMiddleware:
    """Correlate requests and apply browser controls without logging sensitive input."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = uuid.uuid4()
        request.correlation_id = correlation_id  # type: ignore[attr-defined]
        try:
            response = self.get_response(request)
        except Exception:
            logger.exception(
                "request_failed correlation_id=%s method=%s path=%s",
                correlation_id,
                request.method,
                request.path,
            )
            raise

        response["X-Correlation-ID"] = str(correlation_id)
        response["Content-Security-Policy"] = settings.CONTENT_SECURITY_POLICY
        response["Permissions-Policy"] = settings.PERMISSIONS_POLICY
        response["X-Permitted-Cross-Domain-Policies"] = "none"

        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            patch_cache_control(response, no_store=True, private=True)
            patch_vary_headers(response, ("Cookie",))
        return response
