from __future__ import annotations

from unittest.mock import patch

from django.test import Client
from django.urls import reverse


def test_health_endpoints_do_not_cache_operational_state(client: Client) -> None:
    live = client.get(reverse("health-live"))
    assert live.status_code == 200
    assert live["Cache-Control"] == "no-store"
    assert live["X-Correlation-ID"]

    with patch("apps.core.views.connection.ensure_connection"):
        ready = client.get(reverse("health-ready"))
    assert ready.status_code == 200
    assert ready["Cache-Control"] == "no-store"


def test_public_login_marks_the_demo_as_synthetic_and_non_clinical(client: Client) -> None:
    response = client.get(reverse("accounts:login"))
    content = response.content.decode()
    assert response.status_code == 200
    assert "DEMO PÚBLICA — DATOS SINTÉTICOS" in content
    assert "No usa información de pacientes" in content
