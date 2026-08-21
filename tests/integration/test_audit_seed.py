from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.audits.demo_seed import demo_audit_uuid
from apps.audits.models import (
    AuditExecution,
    AuditPlan,
    AuditResponse,
    Checklist,
    Finding,
    FindingEvidence,
)

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_audit_seed_is_deterministic_idempotent_and_matches_contract(
    admin_user: User,
) -> None:
    call_command("seed_organizations_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_audits_demo", actor=admin_user.username, dataset_version="1")
    first = (
        AuditPlan.objects.count(),
        Checklist.objects.count(),
        AuditExecution.objects.count(),
        AuditResponse.objects.count(),
        Finding.objects.count(),
        FindingEvidence.objects.count(),
    )
    call_command("seed_audits_demo", actor=admin_user.username, dataset_version="1")
    assert first == (12, 3, 12, 180, 180, 12)
    assert (
        AuditPlan.objects.count(),
        Checklist.objects.count(),
        AuditExecution.objects.count(),
        AuditResponse.objects.count(),
        Finding.objects.count(),
        FindingEvidence.objects.count(),
    ) == first
    assert AuditPlan.objects.get(code="AUD-01").pk == demo_audit_uuid("plan:AUD-01")
