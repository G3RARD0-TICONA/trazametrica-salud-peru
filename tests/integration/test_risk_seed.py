from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.risks.demo_seed import demo_risk_uuid
from apps.risks.models import (
    Control,
    ControlReview,
    ControlVersion,
    Risk,
    RiskActionLink,
    RiskAssessment,
    RiskControl,
    RiskFindingLink,
    RiskIndicatorLink,
)

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_risk_seed_is_deterministic_idempotent_and_matches_contract(
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
    call_command("seed_audits_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_improvements_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_risks_demo", actor=admin_user.username, dataset_version="1")
    first = (
        Risk.objects.count(),
        RiskAssessment.objects.count(),
        Control.objects.count(),
        ControlVersion.objects.count(),
        RiskControl.objects.count(),
        ControlReview.objects.count(),
        RiskIndicatorLink.objects.count(),
        RiskFindingLink.objects.count(),
        RiskActionLink.objects.count(),
    )
    call_command("seed_risks_demo", actor=admin_user.username, dataset_version="1")
    assert first == (20, 24, 12, 12, 24, 18, 20, 12, 12)
    assert (
        Risk.objects.count(),
        RiskAssessment.objects.count(),
        Control.objects.count(),
        ControlVersion.objects.count(),
        RiskControl.objects.count(),
        ControlReview.objects.count(),
        RiskIndicatorLink.objects.count(),
        RiskFindingLink.objects.count(),
        RiskActionLink.objects.count(),
    ) == first
    assert Risk.objects.get(code="RSK-001").pk == demo_risk_uuid("risk:001")
