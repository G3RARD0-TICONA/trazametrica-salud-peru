from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.imports.demo_seed import seed_import_templates

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_import_catalog_requires_create_capability(client: Client, regular_user: User) -> None:
    client.force_login(regular_user)
    assert client.get(reverse("imports:catalog")).status_code == 403


def test_data_loader_can_download_identified_xlsx(
    client: Client, admin_user: User, regular_user: User, organization: object
) -> None:
    role = Role.objects.create(
        code="DATA_LOADER",
        name="Carga de datos",
        created_by=admin_user,
        updated_by=admin_user,
    )
    assign_role(
        actor=admin_user,
        user=regular_user,
        role=role,
        valid_from=timezone.localdate(),
    )
    seed_import_templates(actor=admin_user)
    client.force_login(regular_user)
    catalog = client.get(reverse("imports:catalog"))
    assert catalog.status_code == 200
    assert "DATOS SINTÉTICOS" in catalog.content.decode()
    version = catalog.context["templates"][0].effective_versions[0]
    response = client.get(reverse("imports:download", kwargs={"version_id": version.pk}))
    assert response.status_code == 200
    assert response.content.startswith(b"PK")
    assert response["X-Content-Type-Options"] == "nosniff"
