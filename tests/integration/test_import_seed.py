from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.imports.demo_seed import demo_import_uuid
from apps.imports.models import ImportTemplate, ImportTemplateVersion, TemplateVersionStatus

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_import_seed_is_deterministic_idempotent_and_matches_contract(admin_user: User) -> None:
    call_command("seed_organizations_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_import_templates_demo", actor=admin_user.username, dataset_version="1")
    first = (ImportTemplate.objects.count(), ImportTemplateVersion.objects.count())
    call_command("seed_import_templates_demo", actor=admin_user.username, dataset_version="1")
    assert first == (4, 4)
    assert (ImportTemplate.objects.count(), ImportTemplateVersion.objects.count()) == first
    assert ImportTemplateVersion.objects.filter(status=TemplateVersionStatus.EFFECTIVE).count() == 4
    assert ImportTemplate.objects.get(code="IMP-KPI").pk == demo_import_uuid("template:IMP-KPI")
