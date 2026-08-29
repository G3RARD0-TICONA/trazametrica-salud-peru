from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.reports.demo_seed import seed_reports
from apps.reports.models import ExportContract

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def _assign(*, admin_user: User, user: User, code: str) -> None:
    role = Role.objects.create(
        code=code,
        name=f"Rol {code}",
        created_by=admin_user,
        updated_by=admin_user,
    )
    assign_role(actor=admin_user, user=user, role=role, valid_from=timezone.localdate())


def test_report_dashboard_and_export_respect_capabilities(
    client: Client, admin_user: User, regular_user: User
) -> None:
    seed_reports(actor=admin_user)
    client.force_login(regular_user)
    assert client.get(reverse("reports:dashboard")).status_code == 403

    _assign(admin_user=admin_user, user=regular_user, code="DATA_LOADER")
    dashboard = client.get(reverse("reports:dashboard"))
    assert dashboard.status_code == 200
    assert b"DATOS SINT" in dashboard.content
    assert b"Solo consulta" in dashboard.content

    contract = ExportContract.objects.get(code="RPT-DASHBOARD-PDF")
    assert (
        client.post(reverse("reports:export-contract", args=[contract.pk]), {}).status_code == 403
    )

    _assign(admin_user=admin_user, user=regular_user, code="QUALITY_MANAGER")
    response = client.post(reverse("reports:export-contract", args=[contract.pk]), {})
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["X-Export-Run"]
    assert len(response["X-Export-SHA256"]) == 64
