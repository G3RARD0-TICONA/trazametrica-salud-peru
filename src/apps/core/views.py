from django.db import connection
from django.http import HttpRequest, JsonResponse


def live(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok", "service": "web"})


def ready(request: HttpRequest) -> JsonResponse:
    try:
        connection.ensure_connection()
    except Exception:  # noqa: BLE001
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})

