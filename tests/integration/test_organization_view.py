from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.organizations.models import Organization, Site
from apps.organizations.services import create_service

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_user_without_view_capability_is_denied(
    client: Client,
    regular_user: User,
) -> None:
    assert client.login(username=regular_user.username, password="Clave-Sintetica-2026")
    assert client.get(reverse("organizations:structure")).status_code == 403


def test_viewer_can_read_active_organization_structure(
    client: Client,
    admin_user: User,
    regular_user: User,
    viewer_role: Role,
    organization: Organization,
    site: Site,
) -> None:
    create_service(
        actor=admin_user,
        site=site,
        code="SER-VISTA",
        name="Servicio Sintético Visible",
    )
    assign_role(
        actor=admin_user,
        user=regular_user,
        role=viewer_role,
        valid_from=timezone.localdate(),
    )
    assert client.login(username=regular_user.username, password="Clave-Sintetica-2026")
    response = client.get(reverse("organizations:structure"))
    content = response.content.decode()
    assert response.status_code == 200
    assert organization.name in content
    assert site.name in content
    assert "Servicio Sintético Visible" in content
    assert "DATOS SINTÉTICOS" in content
