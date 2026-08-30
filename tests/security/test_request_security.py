from __future__ import annotations

import re

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.auditlog.models import AuditEvent, EventResult

pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.security]


def test_public_response_has_browser_security_headers(client: Client) -> None:
    response = client.get(reverse("health-live"))

    assert response.status_code == 200
    assert re.fullmatch(r"[0-9a-f-]{36}", response.headers["X-Correlation-ID"])
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Permissions-Policy"].startswith("camera=()")
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_authenticated_pages_are_not_browser_cached(
    client: Client, admin_user: User
) -> None:
    client.force_login(admin_user)
    response = client.get(reverse("accounts:home"))

    assert response.status_code == 200
    cache_control = response.headers["Cache-Control"]
    assert "no-store" in cache_control
    assert "private" in cache_control
    assert "Cookie" in response.headers["Vary"]


def test_denied_capability_is_persisted_without_query_or_body(
    client: Client, regular_user: User
) -> None:
    client.force_login(regular_user)
    response = client.get(f"{reverse('organizations:structure')}?token=no-registrar")

    assert response.status_code == 403
    event = AuditEvent.objects.get(action="capability.denied")
    assert event.actor == regular_user
    assert event.result == EventResult.DENIED
    assert event.object_type == "authorization"
    assert event.context == {"method": "GET", "path": reverse("organizations:structure")}
    assert "token" not in event.reason
    assert "token" not in str(event.context)


def test_csrf_is_required_for_authenticated_mutation(admin_user: User) -> None:
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(admin_user)

    response = csrf_client.post(reverse("accounts:logout"))

    assert response.status_code == 403
