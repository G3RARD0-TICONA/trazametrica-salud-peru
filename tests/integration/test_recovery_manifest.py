from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

from apps.accounts.models import User
from apps.core.recovery import manifest_matches, recovery_manifest

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_recovery_manifest_is_stable_for_unchanged_database(admin_user: User) -> None:
    first = recovery_manifest()
    second = recovery_manifest()

    assert first["database_vendor"] == "postgresql"
    assert first["table_counts"]["accounts.User"] == 1
    assert len(first["file_manifest_hash"]) == 64
    assert manifest_matches(first, second)


def test_recovery_command_detects_a_changed_database(
    admin_user: User, tmp_path: Path
) -> None:
    expected = recovery_manifest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(expected), encoding="utf-8")
    call_command("recovery_manifest", compare=manifest_path)

    User.objects.create_user(
        username="restauracion_sintetica",
        password="Clave-Sintetica-2026",
        email="restauracion@example.invalid",
        created_by=admin_user,
        updated_by=admin_user,
    )
    with pytest.raises(CommandError, match="no coincide"):
        call_command("recovery_manifest", compare=manifest_path)
