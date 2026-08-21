from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.documents.models import DocumentType
from apps.documents.services import create_document
from apps.organizations.models import Area, Organization

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_document_catalog_requires_view_capability(
    client: Client,
    regular_user: User,
) -> None:
    client.force_login(regular_user)
    response = client.get(reverse("documents:catalog"))
    assert response.status_code == 403


def test_viewer_can_see_synthetic_document_catalog(
    client: Client,
    admin_user: User,
    regular_user: User,
    organization: Organization,
    area: Area,
) -> None:
    role = Role.objects.create(
        code="VIEWER",
        name="Consulta",
        created_by=admin_user,
        updated_by=admin_user,
    )
    assign_role(
        actor=admin_user,
        user=regular_user,
        role=role,
        valid_from=timezone.localdate(),
    )
    create_document(
        actor=admin_user,
        organization=organization,
        responsible_area=area,
        code="DOC-VISTA",
        title="Documento visible sintético",
        document_type=DocumentType.OTHER,
    )
    client.force_login(regular_user)
    response = client.get(reverse("documents:catalog"))
    assert response.status_code == 200
    assert "DATOS SINTÉTICOS" in response.content.decode()
    assert "DOC-VISTA" in response.content.decode()

