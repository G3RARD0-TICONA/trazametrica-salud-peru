from __future__ import annotations

import hashlib

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.reports.models import DatasetCode, ExportContractStatus, ExportFormat, ExportRun
from apps.reports.selectors import ReportFilters
from apps.reports.services import create_export_contract, generate_export, publish_export_contract

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


@pytest.mark.parametrize(
    ("export_format", "signature"),
    [(ExportFormat.CSV, b"\xef\xbb\xbf"), (ExportFormat.XLSX, b"PK"), (ExportFormat.PDF, b"%PDF")],
)
def test_published_contract_generates_audited_artifact(
    admin_user: User, export_format: str, signature: bytes
) -> None:
    contract = create_export_contract(
        actor=admin_user,
        code=f"RPT-DASH-{export_format}",
        name="Tablero sintético",
        dataset=DatasetCode.DASHBOARD,
        export_format=export_format,
    )
    contract = publish_export_contract(actor=admin_user, contract=contract)
    artifact = generate_export(
        actor=admin_user,
        contract=contract,
        filters=ReportFilters(status="published"),
    )
    assert artifact.content.startswith(signature)
    assert artifact.run.row_count >= 1
    assert artifact.run.output_hash == hashlib.sha256(artifact.content).hexdigest()
    assert artifact.run.file_asset.storage_key.startswith("reports/")
    assert artifact.run.file_asset.synthetic_confirmed is True
    assert AuditEvent.objects.filter(action="report.exported", object_id=artifact.run.pk).exists()


def test_contract_publication_supersedes_previous_version(admin_user: User) -> None:
    first = create_export_contract(
        actor=admin_user,
        code="RPT-VERSIONED",
        name="Primera versión",
        dataset=DatasetCode.DASHBOARD,
        export_format=ExportFormat.CSV,
    )
    publish_export_contract(actor=admin_user, contract=first)
    second = create_export_contract(
        actor=admin_user,
        code="RPT-VERSIONED",
        name="Segunda versión",
        dataset=DatasetCode.DASHBOARD,
        export_format=ExportFormat.CSV,
    )
    second = publish_export_contract(actor=admin_user, contract=second)
    first.refresh_from_db()
    assert first.status == ExportContractStatus.SUPERSEDED
    assert second.version_no == 2
    first.name = "Cambio prohibido"
    with pytest.raises(ValidationError, match="inmutable"):
        first.save()


def test_export_requires_permission_and_published_contract(
    admin_user: User, regular_user: User
) -> None:
    contract = create_export_contract(
        actor=admin_user,
        code="RPT-PROTECTED",
        name="Reporte protegido",
        dataset=DatasetCode.DASHBOARD,
        export_format=ExportFormat.CSV,
    )
    with pytest.raises(PermissionDenied, match="capacidad"):
        generate_export(actor=regular_user, contract=contract, filters=ReportFilters())
    with pytest.raises(ValidationError, match="publicado"):
        generate_export(actor=admin_user, contract=contract, filters=ReportFilters())
    assert ExportRun.objects.count() == 0
