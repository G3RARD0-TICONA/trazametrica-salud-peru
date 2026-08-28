from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.organizations.models import Area, Organization
from apps.risks.services import create_risk

from .test_risk_services import process_for_risk, risk_actors

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_risk_catalog_and_detail_require_report_permission(
    client: Client,
    admin_user: User,
    regular_user: User,
    organization: Organization,
    area: Area,
) -> None:
    manager, owner, _reviewer, _approver = risk_actors(admin_user, "VIEW")
    process = process_for_risk(
        admin_user=admin_user, organization=organization, area=area, suffix="VIEW"
    )
    risk = create_risk(
        actor=manager,
        organization=organization,
        process=process,
        code="RSK-VIEW",
        cause="Causa administrativa sintética.",
        event="Evento demostrativo.",
        consequence="Consecuencia ficticia.",
        owner=owner,
    )
    client.force_login(regular_user)
    assert client.get(reverse("risks:catalog")).status_code == 403
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
    catalog = client.get(reverse("risks:catalog"))
    detail = client.get(reverse("risks:detail", args=[risk.pk]))
    assert catalog.status_code == 200
    assert detail.status_code == 200
    assert b"DATOS SINT" in catalog.content
    assert b"RSK-VIEW" in detail.content
