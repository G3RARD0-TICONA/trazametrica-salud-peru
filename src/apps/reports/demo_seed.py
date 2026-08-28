from __future__ import annotations

import uuid
from datetime import UTC, datetime

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User

from .models import DatasetCode, ExportConsumer, ExportContract, ExportContractStatus, ExportFormat
from .schemas import schema_for
from .services import schema_hash

DEMO_NAMESPACE = uuid.UUID("bc9f15d2-54d1-59d7-95ac-30db7017ff9d")
DEMO_PUBLISHED_AT = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)

CONTRACT_CATALOG = (
    (
        "RPT-DASHBOARD-PDF",
        "Tablero ejecutivo KPI",
        DatasetCode.DASHBOARD,
        ExportFormat.PDF,
        ExportConsumer.GENERAL,
    ),
    (
        "RPT-DASHBOARD-XLSX",
        "Tablero KPI en Excel",
        DatasetCode.DASHBOARD,
        ExportFormat.XLSX,
        ExportConsumer.GENERAL,
    ),
    (
        "RPT-KPI-XLSX",
        "Resultados de indicadores",
        DatasetCode.INDICATOR_RESULTS,
        ExportFormat.XLSX,
        ExportConsumer.GENERAL,
    ),
    (
        "RPT-KPI-PBI-CSV",
        "Resultados KPI para Power BI Desktop",
        DatasetCode.INDICATOR_RESULTS,
        ExportFormat.CSV,
        ExportConsumer.POWER_BI_DESKTOP,
    ),
    (
        "RPT-RISK-XLSX",
        "Matriz de riesgos y controles",
        DatasetCode.RISKS,
        ExportFormat.XLSX,
        ExportConsumer.GENERAL,
    ),
    (
        "RPT-FINDING-PDF",
        "Reporte de hallazgos",
        DatasetCode.FINDINGS,
        ExportFormat.PDF,
        ExportConsumer.GENERAL,
    ),
    (
        "RPT-ACTION-CSV",
        "Acciones correctivas",
        DatasetCode.CORRECTIVE_ACTIONS,
        ExportFormat.CSV,
        ExportConsumer.GENERAL,
    ),
)


def demo_report_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


@transaction.atomic
def seed_reports(*, actor: User, dataset_version: str = "1") -> dict[str, int]:
    if dataset_version != "1":
        raise ValidationError("La versión de semilla de reportes no está soportada.")
    for code, name, dataset, export_format, consumer in CONTRACT_CATALOG:
        definition = schema_for(dataset)
        contract, created = ExportContract.objects.get_or_create(
            id=demo_report_uuid(f"contract:{code}:1"),
            defaults={
                "code": code,
                "version_no": 1,
                "name": name,
                "dataset": dataset,
                "format": export_format,
                "consumer": consumer,
                "schema_definition": definition,
                "schema_hash": schema_hash(definition),
                "status": ExportContractStatus.PUBLISHED,
                "published_at": DEMO_PUBLISHED_AT,
                "published_by": actor,
                "created_by": actor,
                "updated_by": actor,
            },
        )
        if created:
            contract.full_clean()
    return {
        "contracts": ExportContract.objects.filter(status=ExportContractStatus.PUBLISHED).count()
    }
