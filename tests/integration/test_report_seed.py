from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.imports.xlsx import parse_workbook
from apps.reports.demo_seed import demo_report_uuid
from apps.reports.models import ExportConsumer, ExportContract, ExportContractStatus, ExportFormat
from apps.reports.selectors import ReportFilters
from apps.reports.services import generate_export

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_report_seed_is_deterministic_idempotent_and_power_bi_ready(admin_user: User) -> None:
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
    call_command("seed_reports_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_reports_demo", actor=admin_user.username, dataset_version="1")
    assert ExportContract.objects.count() == 7
    assert ExportContract.objects.filter(status=ExportContractStatus.PUBLISHED).count() == 7
    power_bi = ExportContract.objects.get(consumer=ExportConsumer.POWER_BI_DESKTOP)
    assert power_bi.code == "RPT-KPI-PBI-CSV"
    assert power_bi.pk == demo_report_uuid("contract:RPT-KPI-PBI-CSV:1")
    assert power_bi.schema_definition["columns"][0]["name"] == "synthetic_marker"
    artifacts = [
        generate_export(actor=admin_user, contract=contract, filters=ReportFilters())
        for contract in ExportContract.objects.order_by("code")
    ]
    assert len(artifacts) == 7
    assert any(artifact.run.row_count == 0 for artifact in artifacts)
    assert any(artifact.run.row_count > 0 for artifact in artifacts)
    for artifact in artifacts:
        if artifact.run.contract.format == ExportFormat.XLSX:
            assert parse_workbook(artifact.content).marker == "DATOS SINTÉTICOS"
        elif artifact.run.contract.format == ExportFormat.CSV and artifact.run.row_count == 0:
            assert artifact.content.startswith(b"\xef\xbb\xbfsynthetic_marker,")
        else:
            assert b"DATOS SINT" in artifact.content
