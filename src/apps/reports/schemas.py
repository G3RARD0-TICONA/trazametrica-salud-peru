from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import DatasetCode

METADATA_COLUMNS: list[dict[str, Any]] = [
    {"name": "synthetic_marker", "type": "text", "required": True},
    {"name": "contract_code", "type": "text", "required": True},
    {"name": "contract_version", "type": "integer", "required": True},
    {"name": "schema_hash", "type": "text", "required": True},
    {"name": "generated_at_utc", "type": "datetime", "required": True},
    {"name": "filters_json", "type": "text", "required": True},
]

DATASET_COLUMNS: dict[str, list[dict[str, Any]]] = {
    DatasetCode.DASHBOARD: [
        {"name": "metric", "type": "text", "required": True},
        {"name": "status", "type": "text", "required": True},
        {"name": "value", "type": "integer", "required": True},
    ],
    DatasetCode.INDICATOR_RESULTS: [
        {"name": "organization_code", "type": "text", "required": True},
        {"name": "site_code", "type": "text", "required": False},
        {"name": "service_code", "type": "text", "required": False},
        {"name": "process_code", "type": "text", "required": True},
        {"name": "indicator_code", "type": "text", "required": True},
        {"name": "indicator_name", "type": "text", "required": True},
        {"name": "indicator_version", "type": "integer", "required": True},
        {"name": "period_start", "type": "date", "required": True},
        {"name": "period_end", "type": "date", "required": True},
        {"name": "value", "type": "decimal", "required": True},
        {"name": "unit", "type": "text", "required": True},
        {"name": "performance_status", "type": "text", "required": True},
        {"name": "result_status", "type": "text", "required": True},
    ],
    DatasetCode.RISKS: [
        {"name": "organization_code", "type": "text", "required": True},
        {"name": "process_code", "type": "text", "required": True},
        {"name": "risk_code", "type": "text", "required": True},
        {"name": "event", "type": "text", "required": True},
        {"name": "owner", "type": "text", "required": True},
        {"name": "risk_status", "type": "text", "required": True},
        {"name": "inherent_level", "type": "integer", "required": False},
        {"name": "inherent_band", "type": "text", "required": False},
        {"name": "residual_level", "type": "integer", "required": False},
        {"name": "residual_band", "type": "text", "required": False},
        {"name": "next_review_date", "type": "date", "required": False},
    ],
    DatasetCode.FINDINGS: [
        {"name": "organization_code", "type": "text", "required": True},
        {"name": "audit_code", "type": "text", "required": True},
        {"name": "finding_code", "type": "text", "required": True},
        {"name": "finding_type", "type": "text", "required": True},
        {"name": "impact", "type": "text", "required": True},
        {"name": "finding_status", "type": "text", "required": True},
        {"name": "due_date", "type": "date", "required": False},
        {"name": "owner", "type": "text", "required": True},
    ],
    DatasetCode.CORRECTIVE_ACTIONS: [
        {"name": "organization_code", "type": "text", "required": True},
        {"name": "finding_code", "type": "text", "required": True},
        {"name": "action_code", "type": "text", "required": True},
        {"name": "action_status", "type": "text", "required": True},
        {"name": "due_date", "type": "date", "required": True},
        {"name": "owner", "type": "text", "required": True},
        {"name": "is_mandatory", "type": "boolean", "required": True},
    ],
}


def schema_for(dataset: str) -> dict[str, Any]:
    try:
        columns = METADATA_COLUMNS + DATASET_COLUMNS[dataset]
    except KeyError as exc:
        raise ValueError("Conjunto de reporte no soportado.") from exc
    return {
        "dataset": dataset,
        "schema_version": "1.0",
        "synthetic_marker": "DATOS SINTÉTICOS",
        "columns": deepcopy(columns),
    }
