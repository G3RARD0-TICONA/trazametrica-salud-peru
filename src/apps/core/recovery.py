from __future__ import annotations

import hashlib
import json
from typing import Any

from django.apps import apps
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone

from apps.documents.models import FileAsset


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def recovery_manifest() -> dict[str, Any]:
    table_counts: dict[str, int] = {}
    for model in apps.get_models():
        if model._meta.managed and not model._meta.proxy:
            table_counts[model._meta.label] = model._default_manager.count()

    migrations = sorted(
        f"{app}:{name}"
        for app, name in MigrationRecorder(connection).migration_qs.values_list(
            "app", "name"
        )
    )
    assets = list(
        FileAsset.objects.order_by("storage_key").values(
            "storage_key", "sha256", "size_bytes", "scan_status"
        )
    )
    stable_payload = {
        "database_vendor": connection.vendor,
        "migrations": migrations,
        "table_counts": table_counts,
        "file_manifest_hash": hashlib.sha256(canonical_json(assets).encode()).hexdigest(),
    }
    return {
        "schema_version": 1,
        "generated_at_utc": timezone.now().isoformat(),
        **stable_payload,
        "fingerprint": hashlib.sha256(canonical_json(stable_payload).encode()).hexdigest(),
    }


def manifest_matches(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    return bool(expected.get("fingerprint")) and expected.get("fingerprint") == observed.get(
        "fingerprint"
    )
