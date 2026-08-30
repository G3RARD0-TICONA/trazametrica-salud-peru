from __future__ import annotations

import io
import time
import zipfile
from collections.abc import Callable

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.auditlog.models import AuditEvent
from apps.imports.models import (
    ImportJobStatus,
    ImportTemplate,
    ImportTemplateVersion,
    TemplateTargetType,
    TemplateVersionStatus,
)
from apps.imports.services import (
    approve_template_version,
    create_import_template,
    create_template_version,
    promote_import_job,
    receive_and_validate_import,
    submit_template_version,
    template_workbook,
)
from apps.imports.xlsx import generate_workbook
from apps.organizations.models import Organization

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def create_approver(*, admin_user: User) -> User:
    approver = User.objects.create_user(
        username="aprobador_importaciones",
        password="Clave-Sintetica-2026",
        created_by=admin_user,
        updated_by=admin_user,
    )
    role = Role.objects.create(
        code="APPROVER",
        name="Aprobación independiente",
        is_approval_role=True,
        created_by=admin_user,
        updated_by=admin_user,
    )
    assign_role(
        actor=admin_user,
        user=approver,
        role=role,
        valid_from=timezone.localdate(),
    )
    return approver


def sample_schema() -> dict[str, object]:
    return {
        "columns": [
            {
                "name": "record_code",
                "type": "string",
                "required": True,
                "max_length": 50,
                "pattern": "^[A-Z0-9-]+$",
                "unique_in_file": True,
            },
            {"name": "period", "type": "date", "required": True},
            {"name": "value", "type": "decimal", "required": True, "min": 0, "max": 100},
            {
                "name": "status",
                "type": "string",
                "required": True,
                "choices": ["ok", "warning"],
            },
        ]
    }


def effective_template(
    *, admin_user: User, organization: Organization
) -> tuple[ImportTemplate, ImportTemplateVersion, User]:
    template = create_import_template(
        actor=admin_user,
        organization=organization,
        code=" imp-test ",
        name="Plantilla sintética de prueba",
        target_type=TemplateTargetType.KPI_OBSERVATIONS,
    )
    version = create_template_version(
        actor=admin_user,
        template=template,
        schema_definition=sample_schema(),
    )
    submit_template_version(actor=admin_user, version=version)
    approver = create_approver(admin_user=admin_user)
    version = approve_template_version(
        actor=approver,
        version=version,
        valid_from=timezone.localdate(),
        reason="Esquema sintético conforme",
    )
    return template, version, approver


def workbook(version: ImportTemplateVersion, rows: list[list[object]]) -> bytes:
    return generate_workbook(
        template_code=version.template.code,
        version_no=version.version_no,
        schema_hash=version.schema_hash,
        schema=version.schema_definition,
        data_rows=rows,
    )


def replace_part(content: bytes, path: str, transform: Callable[[bytes], bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(content)) as original, zipfile.ZipFile(output, "w") as altered:
        for info in original.infolist():
            value = original.read(info.filename)
            if info.filename == path:
                value = transform(value)
            altered.writestr(info, value)
    return output.getvalue()


def test_template_code_version_hash_and_independent_approval(
    admin_user: User, organization: Organization
) -> None:
    template = create_import_template(
        actor=admin_user,
        organization=organization,
        code=" imp-001 ",
        name="Plantilla sintética",
        target_type=TemplateTargetType.KPI_OBSERVATIONS,
    )
    assert template.code == "IMP-001"
    version = create_template_version(
        actor=admin_user,
        template=template,
        schema_definition=sample_schema(),
    )
    assert version.version_no == 1
    assert len(version.schema_hash) == 64
    submit_template_version(actor=admin_user, version=version)
    with pytest.raises(PermissionDenied, match="propia plantilla"):
        approve_template_version(
            actor=admin_user,
            version=version,
            valid_from=timezone.localdate(),
        )


def test_downloaded_workbook_is_identified_and_deterministic(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    first = template_workbook(version)
    second = template_workbook(version)
    assert first == second
    assert first.startswith(b"PK")
    assert len(first) < 10 * 1024 * 1024


def test_valid_import_is_accepted_promoted_and_audited(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    content = workbook(
        version,
        [["REG-001", "2026-01-31", "45.5", "ok"], ["REG-002", "2026-02-28", "50", "warning"]],
    )
    job = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="datos-sinteticos.xlsx",
        content=content,
        synthetic_confirmed=True,
    )
    assert job.status == ImportJobStatus.ACCEPTED
    assert (job.row_count, job.error_count, job.rows.count()) == (2, 0, 2)
    processed = promote_import_job(actor=admin_user, job=job)
    assert processed.status == ImportJobStatus.PROCESSED
    assert processed.promoted_at is not None
    assert AuditEvent.objects.filter(action="import_job.processed").exists()


def test_invalid_import_is_rejected_with_actionable_errors_and_no_promotion(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    content = workbook(
        version,
        [
            ["reg lowercase", "2099-01-01", "101", "invalid"],
            ["reg lowercase", "fecha", "texto", "ok"],
        ],
    )
    job = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="errores-sinteticos.xlsx",
        content=content,
        synthetic_confirmed=True,
    )
    assert job.status == ImportJobStatus.REJECTED
    assert job.error_count >= 7
    assert {error.rule_code for row in job.rows.all() for error in row.errors.all()} >= {
        "pattern",
        "future_date",
        "max",
        "choice",
        "duplicate_value",
        "type_date",
        "type_decimal",
    }
    with pytest.raises(ValidationError, match="aceptada"):
        promote_import_job(actor=admin_user, job=job)


def test_excel_formula_is_rejected_as_blocking_content(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    content = workbook(version, [["REG-001", "2026-01-01", "10", "ok"]])

    def insert_formula(xml: bytes) -> bytes:
        start = b'<c r="C3" s="1" t="inlineStr"><is><t>10</t></is></c>'
        return xml.replace(start, b'<c r="C3"><f>5+5</f><v>10</v></c>')

    altered = replace_part(content, "xl/worksheets/sheet1.xml", insert_formula)
    job = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="formula-prohibida.xlsx",
        content=altered,
        synthetic_confirmed=True,
    )
    assert job.status == ImportJobStatus.REJECTED
    assert job.rows.get().errors.get(rule_code="formula_not_allowed").column_name == "value"


def test_unknown_template_identity_is_rejected_atomically(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    content = generate_workbook(
        template_code="IMP-OTRA",
        version_no=version.version_no,
        schema_hash=version.schema_hash,
        schema=version.schema_definition,
        data_rows=[["REG-001", "2026-01-01", "10", "ok"]],
    )
    job = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="identidad-incorrecta.xlsx",
        content=content,
        synthetic_confirmed=True,
    )
    assert job.status == ImportJobStatus.REJECTED
    assert job.rows.get().errors.get().rule_code == "template_identity"


def test_duplicate_accepted_file_links_antecedent(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    content = workbook(version, [["REG-001", "2026-01-01", "10", "ok"]])
    first = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="primera.xlsx",
        content=content,
        synthetic_confirmed=True,
    )
    duplicate = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="repetida.xlsx",
        content=content,
        synthetic_confirmed=True,
    )
    assert first.status == ImportJobStatus.ACCEPTED
    assert duplicate.status == ImportJobStatus.DUPLICATE
    assert duplicate.duplicate_of == first
    assert duplicate.rows.count() == 0


def test_rejected_job_can_be_retried_traceably(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    rejected = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="rechazada.xlsx",
        content=workbook(version, [["", "2026-01-01", "10", "ok"]]),
        synthetic_confirmed=True,
    )
    retried = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="corregida.xlsx",
        content=workbook(version, [["REG-001", "2026-01-01", "10", "ok"]]),
        synthetic_confirmed=True,
        retry_of=rejected,
    )
    assert rejected.status == ImportJobStatus.REJECTED
    assert retried.status == ImportJobStatus.ACCEPTED
    assert retried.retry_of == rejected
    assert retried.attempt_count == 2


def test_synthetic_confirmation_and_permission_are_mandatory(
    admin_user: User,
    regular_user: User,
    organization: Organization,
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    content = workbook(version, [["REG-001", "2026-01-01", "10", "ok"]])
    with pytest.raises(ValidationError, match="confirmar"):
        receive_and_validate_import(
            actor=admin_user,
            organization=organization,
            template_version=version,
            original_name="archivo.xlsx",
            content=content,
            synthetic_confirmed=False,
        )
    with pytest.raises(PermissionDenied):
        receive_and_validate_import(
            actor=regular_user,
            organization=organization,
            template_version=version,
            original_name="archivo.xlsx",
            content=content,
            synthetic_confirmed=True,
        )


def test_real_email_is_blocked_without_copying_it_to_error_message(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    content = workbook(
        version,
        [["persona@example.com", "2026-01-01", "10", "ok"]],
    )
    job = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="dato-inseguro.xlsx",
        content=content,
        synthetic_confirmed=True,
    )
    error = job.rows.get().errors.get(rule_code="unsafe_real_data")
    assert job.status == ImportJobStatus.REJECTED
    assert "persona@example.com" not in error.message


def test_new_template_version_supersedes_previous_version(
    admin_user: User, organization: Organization
) -> None:
    template, first, approver = effective_template(admin_user=admin_user, organization=organization)
    second = create_template_version(
        actor=admin_user,
        template=template,
        schema_definition=sample_schema(),
    )
    submit_template_version(actor=admin_user, version=second)
    second = approve_template_version(
        actor=approver,
        version=second,
        valid_from=timezone.localdate(),
    )
    first.refresh_from_db()
    assert first.status == TemplateVersionStatus.SUPERSEDED
    assert first.valid_to == timezone.localdate()
    assert second.status == TemplateVersionStatus.EFFECTIVE


def test_import_records_are_not_physically_deleted(
    admin_user: User, organization: Organization
) -> None:
    template, version, _ = effective_template(admin_user=admin_user, organization=organization)
    job = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="archivo.xlsx",
        content=workbook(version, [["REG-001", "2026-01-01", "10", "ok"]]),
        synthetic_confirmed=True,
    )
    with pytest.raises(ValidationError, match="físicamente"):
        template.delete()
    with pytest.raises(ValidationError, match="físicamente"):
        version.delete()
    with pytest.raises(ValidationError, match="físicamente"):
        job.delete()


def test_expected_p10_tables_are_declared() -> None:
    assert ImportTemplate._meta.db_table == "imports_template"
    assert ImportTemplateVersion._meta.db_table == "imports_template_version"
    assert ImportJobStatus.ACCEPTED == "accepted"


@pytest.mark.performance
def test_reference_import_of_ten_thousand_rows_finishes_within_sixty_seconds(
    admin_user: User, organization: Organization
) -> None:
    _, version, _ = effective_template(admin_user=admin_user, organization=organization)
    content = workbook(
        version,
        [[f"REG-{number:05d}", "2026-01-01", str(number % 101), "ok"] for number in range(10_000)],
    )
    started = time.monotonic()
    job = receive_and_validate_import(
        actor=admin_user,
        organization=organization,
        template_version=version,
        original_name="diez-mil-sinteticas.xlsx",
        content=content,
        synthetic_confirmed=True,
    )
    elapsed = time.monotonic() - started
    assert job.status == ImportJobStatus.ACCEPTED
    assert job.row_count == 10_000
    assert elapsed <= 60
