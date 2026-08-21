from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.audits.services import create_audit_plan
from apps.organizations.models import Organization

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_audit_catalog_requires_report_permission_and_marks_synthetic_data(
    client: Client,
    admin_user: User,
    regular_user: User,
    organization: Organization,
) -> None:
    plan = create_audit_plan(
        actor=admin_user,
        organization=organization,
        code="AUD-VIEW",
        scope="Alcance visible sintético",
        criteria="Criterio visible sintético",
        lead_auditor=admin_user,
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate(),
    )
    client.force_login(regular_user)
    assert client.get(reverse("audits:catalog")).status_code == 403
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
    catalog = client.get(reverse("audits:catalog"))
    detail = client.get(reverse("audits:detail", args=[plan.pk]))
    assert catalog.status_code == 200
    assert detail.status_code == 200
    assert b"DATOS SINT" in catalog.content
    assert b"AUD-VIEW" in detail.content
