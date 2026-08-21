from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.organizations.models import Area, Organization
from apps.processes.models import ProcessType
from apps.processes.services import create_process, create_process_version

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_process_catalog_requires_view_capability(client: Client, regular_user: User) -> None:
    client.force_login(regular_user)
    assert client.get(reverse("processes:catalog")).status_code == 403


def test_viewer_can_see_catalog_and_process_ficha(
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
    process = create_process(
        actor=admin_user,
        organization=organization,
        owner_area=area,
        code="OPE-VISTA",
        name="Proceso visible sintético",
        process_type=ProcessType.OPERATIONAL,
    )
    create_process_version(
        actor=admin_user,
        process=process,
        objective="Objetivo visible sintético",
        scope="Alcance visible sintético",
    )
    client.force_login(regular_user)
    catalog = client.get(reverse("processes:catalog"))
    detail = client.get(reverse("processes:detail", kwargs={"process_id": process.pk}))
    assert catalog.status_code == detail.status_code == 200
    assert "DATOS SINTÉTICOS" in catalog.content.decode()
    assert "OPE-VISTA" in catalog.content.decode()
    assert "Objetivo visible sintético" in detail.content.decode()
