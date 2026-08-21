from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.organizations.demo_seed import demo_uuid
from apps.organizations.models import Area, Organization, Service, Site

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_seed_is_deterministic_idempotent_and_matches_reference_counts(
    admin_user: User,
) -> None:
    call_command("seed_organizations_demo", actor=admin_user.username, dataset_version="1")
    first_counts = (
        Organization.objects.count(),
        Site.objects.count(),
        Service.objects.count(),
        Area.objects.count(),
    )
    call_command("seed_organizations_demo", actor=admin_user.username, dataset_version="1")

    assert first_counts == (1, 3, 20, 12)
    assert (
        Organization.objects.count(),
        Site.objects.count(),
        Service.objects.count(),
        Area.objects.count(),
    ) == first_counts
    assert Organization.objects.get().pk == demo_uuid("organization:demo")
    assert Site.objects.get(code="SED-01").pk == demo_uuid("site:SED-01")
