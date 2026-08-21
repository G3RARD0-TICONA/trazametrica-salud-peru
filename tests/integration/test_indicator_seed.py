from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.indicators.demo_seed import demo_indicator_uuid
from apps.indicators.models import Indicator, IndicatorObservation, IndicatorVersion

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_indicator_seed_is_deterministic_idempotent_and_matches_contract(
    admin_user: User,
) -> None:
    call_command("seed_organizations_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_processes_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_import_templates_demo", actor=admin_user.username, dataset_version="1")
    call_command(
        "seed_indicators_demo",
        actor=admin_user.username,
        dataset_version="1",
        observation_count=1000,
    )
    first = (
        Indicator.objects.count(),
        IndicatorVersion.objects.count(),
        IndicatorObservation.objects.count(),
    )
    call_command(
        "seed_indicators_demo",
        actor=admin_user.username,
        dataset_version="1",
        observation_count=1000,
    )
    assert first == (200, 260, 1000)
    assert (
        Indicator.objects.count(),
        IndicatorVersion.objects.count(),
        IndicatorObservation.objects.count(),
    ) == first
    assert Indicator.objects.get(code="KPI-001").pk == demo_indicator_uuid(
        "indicator:KPI-001"
    )
