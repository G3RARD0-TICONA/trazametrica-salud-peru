from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import Role, User

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_bootstrap_creates_one_admin_and_eight_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "Clave-Bootstrap-2026")
    call_command("bootstrap_access", username="admin_prueba")

    admin = User.objects.get(username="admin_prueba")
    assert admin.is_superuser
    assert admin.check_password("Clave-Bootstrap-2026")
    assert Role.objects.count() == 8
    assert admin.role_assignments.filter(role__code="ADMIN_SYSTEM").count() == 1
