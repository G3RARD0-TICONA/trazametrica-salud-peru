from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.organizations.models import Organization

from .test_improvement_services import build_finding

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_improvement_catalog_and_detail_require_report_permission(
    client: Client,
    admin_user: User,
    regular_user: User,
    organization: Organization,
) -> None:
    _manager, _owner, _approver, finding = build_finding(
        admin_user=admin_user, organization=organization, suffix="P13V"
    )
    client.force_login(regular_user)
    assert client.get(reverse("improvements:catalog")).status_code == 403
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
        valid_from=finding.created_at.date(),
    )
    catalog = client.get(reverse("improvements:catalog"))
    detail = client.get(reverse("improvements:detail", args=[finding.pk]))
    assert catalog.status_code == 200
    assert detail.status_code == 200
    assert b"DATOS SINT" in catalog.content
    assert b"HAL-P13V" in detail.content
