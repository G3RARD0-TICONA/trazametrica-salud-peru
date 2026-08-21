from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.indicators.services import create_indicator
from apps.organizations.models import Area, Organization
from apps.processes.models import ProcessType
from apps.processes.services import create_process

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_indicator_catalog_requires_report_permission_and_marks_synthetic_data(
    client: Client,
    admin_user: User,
    regular_user: User,
    organization: Organization,
    area: Area,
) -> None:
    process = create_process(
        actor=admin_user,
        organization=organization,
        owner_area=area,
        code="PRO-KPI",
        name="Proceso KPI sintético",
        process_type=ProcessType.OPERATIONAL,
    )
    indicator = create_indicator(
        actor=admin_user,
        organization=organization,
        process=process,
        code="KPI-VIEW",
        name="Indicador visible sintético",
        owner=admin_user,
    )
    client.force_login(regular_user)
    assert client.get(reverse("indicators:catalog")).status_code == 403
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
    catalog = client.get(reverse("indicators:catalog"))
    detail = client.get(reverse("indicators:detail", args=[indicator.pk]))
    assert catalog.status_code == 200
    assert detail.status_code == 200
    assert b"DATOS SINT" in catalog.content
    assert b"KPI-VIEW" in detail.content
