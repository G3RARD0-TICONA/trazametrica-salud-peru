from django.db import connection
from django.http import HttpRequest, JsonResponse


def _health_response(payload: dict[str, str], *, status: int = 200) -> JsonResponse:
    response = JsonResponse(payload, status=status)
    response["Cache-Control"] = "no-store"
    return response


def live(request: HttpRequest) -> JsonResponse:
    return _health_response({"status": "ok", "service": "web"})


def ready(request: HttpRequest) -> JsonResponse:
    try:
        connection.ensure_connection()
    except Exception:  # noqa: BLE001
        return _health_response({"status": "unavailable"}, status=503)
    return _health_response({"status": "ready"})
