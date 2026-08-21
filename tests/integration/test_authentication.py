from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import authenticate
from django.db import connection
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role, deactivate_user

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_integration_suite_uses_postgresql() -> None:
    assert connection.vendor == "postgresql"


def test_anonymous_user_is_redirected_to_login(client: Client) -> None:
    response = client.get(reverse("accounts:home"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


def test_active_user_without_current_role_is_denied(
    client: Client,
    regular_user: User,
) -> None:
    assert client.login(username=regular_user.username, password="Clave-Sintetica-2026")
    assert client.get(reverse("accounts:home")).status_code == 403


def test_current_viewer_can_open_dashboard_and_access_profile(
    client: Client,
    admin_user: User,
    regular_user: User,
    viewer_role: Role,
) -> None:
    assign_role(
        actor=admin_user,
        user=regular_user,
        role=viewer_role,
        valid_from=timezone.localdate(),
    )
    assert client.login(username=regular_user.username, password="Clave-Sintetica-2026")

    assert client.get(reverse("accounts:home")).status_code == 200
    profile = client.get(reverse("accounts:access-profile"))
    assert profile.status_code == 200
    assert "VIEWER" in profile.content.decode()


def test_expired_role_does_not_grant_access(
    client: Client,
    admin_user: User,
    regular_user: User,
    viewer_role: Role,
) -> None:
    today = timezone.localdate()
    assign_role(
        actor=admin_user,
        user=regular_user,
        role=viewer_role,
        valid_from=today - timedelta(days=10),
        valid_to=today - timedelta(days=1),
    )
    assert client.login(username=regular_user.username, password="Clave-Sintetica-2026")
    assert client.get(reverse("accounts:home")).status_code == 403


def test_deactivated_user_cannot_authenticate(
    admin_user: User,
    regular_user: User,
) -> None:
    deactivated = deactivate_user(
        actor=admin_user,
        user=regular_user,
        reason="Fin de acceso en escenario sintético.",
    )
    assert not deactivated.is_active
    assert deactivated.deactivation_reason == "Fin de acceso en escenario sintético."
    assert (
        authenticate(
            username=regular_user.username,
            password="Clave-Sintetica-2026",
        )
        is None
    )


def test_health_endpoints_distinguish_liveness_and_readiness(client: Client) -> None:
    live = client.get(reverse("health-live"))
    ready = client.get(reverse("health-ready"))
    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
