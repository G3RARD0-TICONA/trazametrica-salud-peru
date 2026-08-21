from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.audits.models import Finding, FindingStatus
from apps.improvements.demo_seed import demo_improvement_uuid
from apps.improvements.models import (
    ActionEvidence,
    CorrectiveAction,
    CorrectiveActionStatus,
    EffectivenessReview,
    RootCauseAnalysis,
)

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_improvement_seed_is_deterministic_idempotent_and_matches_contract(
    admin_user: User,
) -> None:
    call_command("seed_organizations_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_audits_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_improvements_demo", actor=admin_user.username, dataset_version="1")
    first = (
        RootCauseAnalysis.objects.count(),
        CorrectiveAction.objects.count(),
        ActionEvidence.objects.count(),
        EffectivenessReview.objects.count(),
    )
    call_command("seed_improvements_demo", actor=admin_user.username, dataset_version="1")
    assert first == (12, 24, 18, 15)
    assert (
        RootCauseAnalysis.objects.count(),
        CorrectiveAction.objects.count(),
        ActionEvidence.objects.count(),
        EffectivenessReview.objects.count(),
    ) == first
    assert CorrectiveAction.objects.get(code="ACP-001").pk == demo_improvement_uuid(
        "action:001"
    )
    assert CorrectiveAction.objects.filter(status=CorrectiveActionStatus.CLOSED).count() == 12
    assert Finding.objects.filter(status=FindingStatus.CLOSED).count() == 6
