from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.processes.demo_seed import demo_process_uuid
from apps.processes.models import Process, ProcessType, ProcessVersion, SipocEntry

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_process_seed_is_deterministic_idempotent_and_complete(admin_user: User) -> None:
    call_command("seed_organizations_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_processes_demo", actor=admin_user.username, dataset_version="1")
    first = (Process.objects.count(), ProcessVersion.objects.count(), SipocEntry.objects.count())
    call_command("seed_processes_demo", actor=admin_user.username, dataset_version="1")
    assert first == (100, 100, 500)
    assert (
        Process.objects.count(),
        ProcessVersion.objects.count(),
        SipocEntry.objects.count(),
    ) == first
    assert Process.objects.filter(process_type=ProcessType.STRATEGIC).count() == 10
    assert Process.objects.filter(process_type=ProcessType.OPERATIONAL).count() == 60
    assert Process.objects.filter(process_type=ProcessType.SUPPORT).count() == 30
    assert Process.objects.get(code="EST-001").pk == demo_process_uuid("process:EST-001")
