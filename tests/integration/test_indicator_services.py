from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.auditlog.models import AuditEvent
from apps.documents.models import FileAsset, ScanStatus
from apps.imports.models import (
    ImportJob,
    ImportJobStatus,
    ImportRow,
    ImportTemplate,
    ImportTemplateVersion,
    TemplateTargetType,
    TemplateVersionStatus,
)
from apps.indicators.models import (
    Indicator,
    IndicatorDirection,
    IndicatorFrequency,
    IndicatorObservation,
    IndicatorVersion,
    IndicatorVersionStatus,
    PerformanceStatus,
    ResultInput,
    ResultStatus,
)
from apps.indicators.services import (
    approve_indicator_version,
    calculate_indicator_result,
    create_indicator,
    create_indicator_version,
    deactivate_indicator,
    materialize_kpi_observations,
    publish_indicator_result,
    reject_indicator_result,
    reject_indicator_version,
    submit_indicator_version,
    submit_result_review,
    update_indicator_draft,
)
from apps.organizations.models import Area, Organization, Service, Site
from apps.organizations.services import create_service
from apps.processes.models import Process, ProcessType
from apps.processes.services import create_process

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def create_approver(*, admin_user: User) -> User:
    approver = User.objects.create_user(
        username="aprobador_kpi",
        password="Clave-Sintetica-2026",
        email="aprobador.kpi@example.invalid",
        created_by=admin_user,
        updated_by=admin_user,
    )
    role = Role.objects.create(
        code="APPROVER",
        name="Aprobador KPI",
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


def create_test_process(
    *, admin_user: User, organization: Organization, area: Area
) -> Process:
    return create_process(
        actor=admin_user,
        organization=organization,
        owner_area=area,
        code="PRO-KPI",
        name="Proceso KPI sintético",
        process_type=ProcessType.OPERATIONAL,
    )


def create_test_indicator(
    *, admin_user: User, organization: Organization, area: Area
) -> Indicator:
    process = create_test_process(
        admin_user=admin_user, organization=organization, area=area
    )
    return create_indicator(
        actor=admin_user,
        organization=organization,
        process=process,
        code=" kpi-001 ",
        name="Cumplimiento sintético",
        owner=admin_user,
    )


def create_effective_version(
    *, admin_user: User, approver: User, indicator: Indicator
) -> IndicatorVersion:
    version = create_indicator_version(
        actor=admin_user,
        indicator=indicator,
        purpose="Medir cumplimiento administrativo sintético.",
        unit="%",
        frequency=IndicatorFrequency.MONTHLY,
        direction=IndicatorDirection.HIGHER_IS_BETTER,
        formula_ast={"op": "average", "role": "value"},
        target_value=Decimal("80"),
        warning_threshold=Decimal("60"),
    )
    submit_indicator_version(actor=admin_user, version=version)
    return approve_indicator_version(
        actor=approver,
        version=version,
        valid_from=date(2026, 1, 1),
        reason="Ficha KPI sintética conforme",
    )


def create_import_job(
    *,
    admin_user: User,
    organization: Organization,
    rows: list[dict[str, object]],
) -> ImportJob:
    template, _ = ImportTemplate.objects.get_or_create(
        organization=organization,
        code="IMP-KPI-TEST",
        defaults={
            "name": "Importación KPI de prueba",
            "target_type": TemplateTargetType.KPI_OBSERVATIONS,
            "created_by": admin_user,
            "updated_by": admin_user,
        },
    )
    template_version, _ = ImportTemplateVersion.objects.get_or_create(
        template=template,
        version_no=1,
        defaults={
            "status": TemplateVersionStatus.EFFECTIVE,
            "schema_definition": {"columns": []},
            "schema_hash": "a" * 64,
            "valid_from": date(2026, 1, 1),
            "approved_at": timezone.now(),
            "approved_by": admin_user,
            "created_by": admin_user,
            "updated_by": admin_user,
        },
    )
    digest = hashlib.sha256(f"job-{len(rows)}-{rows}".encode()).hexdigest()
    asset = FileAsset.objects.create(
        storage_key=f"imports/{digest}.xlsx",
        original_name="observaciones-sinteticas.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=1,
        sha256=digest,
        scan_status=ScanStatus.CLEAN,
        synthetic_confirmed=True,
        created_by=admin_user,
        updated_by=admin_user,
    )
    job = ImportJob.objects.create(
        template_version=template_version,
        source_file=asset,
        organization=organization,
        status=ImportJobStatus.PROCESSED,
        file_hash=digest,
        row_count=len(rows),
        error_count=0,
        started_at=timezone.now(),
        finished_at=timezone.now(),
        promoted_at=timezone.now(),
        attempt_count=1,
        created_by=admin_user,
        updated_by=admin_user,
    )
    for position, data in enumerate(rows, start=2):
        ImportRow.objects.create(
            import_job=job,
            row_number=position,
            raw_data=data,
            normalized_hash=hashlib.sha256(str(data).encode()).hexdigest(),
            is_valid=True,
        )
    return job


def observation_rows(*, site: Site, service: Service) -> list[dict[str, object]]:
    return [
        {
            "site_code": site.code,
            "service_code": service.code,
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "value": value,
            "dimension_key": f"DIM-{index}",
        }
        for index, value in enumerate(("70", "90"), start=1)
    ]


def test_indicator_metadata_version_workflow_and_immutability(
    admin_user: User, organization: Organization, area: Area
) -> None:
    indicator = create_test_indicator(
        admin_user=admin_user, organization=organization, area=area
    )
    assert indicator.code == "KPI-001"
    version = create_indicator_version(
        actor=admin_user,
        indicator=indicator,
        purpose="Propósito inicial",
        unit="%",
        frequency=IndicatorFrequency.MONTHLY,
        direction=IndicatorDirection.HIGHER_IS_BETTER,
        formula_ast={"op": "average", "role": "value"},
        target_value=Decimal("80"),
        warning_threshold=Decimal("60"),
    )
    original_hash = version.formula_hash
    updated = update_indicator_draft(
        actor=admin_user,
        version=version,
        purpose="Propósito actualizado",
        unit="%",
        frequency=IndicatorFrequency.MONTHLY,
        direction=IndicatorDirection.HIGHER_IS_BETTER,
        formula_ast={"op": "maximum", "role": "value"},
        target_value=Decimal("80"),
        warning_threshold=Decimal("60"),
    )
    assert updated.formula_hash != original_hash
    submit_indicator_version(actor=admin_user, version=updated)
    with pytest.raises(PermissionDenied, match="propia ficha"):
        approve_indicator_version(
            actor=admin_user, version=updated, valid_from=date(2026, 1, 1)
        )
    approver = create_approver(admin_user=admin_user)
    approved = approve_indicator_version(
        actor=approver, version=updated, valid_from=date(2026, 1, 1)
    )
    assert approved.status == IndicatorVersionStatus.EFFECTIVE
    with pytest.raises(ValidationError, match="borrador"):
        update_indicator_draft(
            actor=admin_user,
            version=approved,
            purpose="Cambio indebido",
            unit="%",
            frequency=IndicatorFrequency.MONTHLY,
            direction=IndicatorDirection.HIGHER_IS_BETTER,
            formula_ast=approved.formula_ast,
            target_value=Decimal("80"),
            warning_threshold=Decimal("60"),
        )
    approved.purpose = "Alteración directa"
    with pytest.raises(ValidationError, match="inmutable"):
        approved.save()


def test_rejection_and_deactivation_require_reason(
    admin_user: User, organization: Organization, area: Area
) -> None:
    indicator = create_test_indicator(
        admin_user=admin_user, organization=organization, area=area
    )
    version = create_indicator_version(
        actor=admin_user,
        indicator=indicator,
        purpose="Propósito",
        unit="unidades",
        frequency=IndicatorFrequency.MONTHLY,
        direction=IndicatorDirection.LOWER_IS_BETTER,
        formula_ast={"op": "sum", "role": "value"},
        target_value=Decimal("20"),
        warning_threshold=Decimal("40"),
    )
    submit_indicator_version(actor=admin_user, version=version)
    with pytest.raises(ValidationError, match="motivo"):
        reject_indicator_version(actor=admin_user, version=version, reason=" ")
    rejected = reject_indicator_version(
        actor=admin_user, version=version, reason="Ajustar fórmula sintética"
    )
    assert rejected.status == IndicatorVersionStatus.DRAFT
    with pytest.raises(ValidationError, match="motivo"):
        deactivate_indicator(actor=admin_user, indicator=indicator, reason="")
    deactivated = deactivate_indicator(
        actor=admin_user, indicator=indicator, reason="Indicador sintético retirado"
    )
    assert not deactivated.is_active


def test_observation_materialization_is_atomic_and_referential(
    admin_user: User,
    organization: Organization,
    area: Area,
    site: Site,
) -> None:
    service = create_service(
        actor=admin_user,
        site=site,
        code="SER-KPI",
        name="Servicio KPI sintético",
    )
    indicator = create_test_indicator(
        admin_user=admin_user, organization=organization, area=area
    )
    job = create_import_job(
        admin_user=admin_user,
        organization=organization,
        rows=observation_rows(site=site, service=service),
    )
    observations = materialize_kpi_observations(
        actor=admin_user, job=job, indicator=indicator
    )
    assert [item.value for item in observations] == [Decimal("70"), Decimal("90")]
    assert IndicatorObservation.objects.filter(import_job=job).count() == 2
    with pytest.raises(ValidationError, match="ya fue materializada"):
        materialize_kpi_observations(actor=admin_user, job=job, indicator=indicator)

    bad_job = create_import_job(
        admin_user=admin_user,
        organization=organization,
        rows=[
            {
                **observation_rows(site=site, service=service)[0],
                "service_code": "NO-EXISTE",
            }
        ],
    )
    with pytest.raises(ValidationError, match="desconocido"):
        materialize_kpi_observations(actor=admin_user, job=bad_job, indicator=indicator)
    assert not IndicatorObservation.objects.filter(import_job=bad_job).exists()


def test_calculation_publication_and_correction_preserve_history(
    admin_user: User,
    organization: Organization,
    area: Area,
    site: Site,
) -> None:
    service = create_service(
        actor=admin_user, site=site, code="SER-KPI", name="Servicio KPI"
    )
    indicator = create_test_indicator(
        admin_user=admin_user, organization=organization, area=area
    )
    approver = create_approver(admin_user=admin_user)
    version = create_effective_version(
        admin_user=admin_user, approver=approver, indicator=indicator
    )
    job = create_import_job(
        admin_user=admin_user,
        organization=organization,
        rows=observation_rows(site=site, service=service),
    )
    observations = materialize_kpi_observations(
        actor=admin_user, job=job, indicator=indicator
    )
    result = calculate_indicator_result(
        actor=admin_user,
        version=version,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        site=site,
        service=service,
        inputs={"value": observations},
    )
    assert result.value == Decimal("80.000000")
    assert result.performance_status == PerformanceStatus.ON_TARGET
    assert ResultInput.objects.filter(result=result).count() == 2
    submit_result_review(actor=admin_user, result=result)
    with pytest.raises(PermissionDenied, match="propio resultado"):
        publish_indicator_result(actor=admin_user, result=result)
    published = publish_indicator_result(
        actor=approver, result=result, reason="Resultado sintético conforme"
    )
    assert published.status == ResultStatus.PUBLISHED

    correction_job = create_import_job(
        admin_user=admin_user,
        organization=organization,
        rows=[
            {
                **observation_rows(site=site, service=service)[0],
                "value": "60",
                "dimension_key": "DIM-CORRECCION",
            }
        ],
    )
    correction_inputs = materialize_kpi_observations(
        actor=admin_user, job=correction_job, indicator=indicator
    )
    correction = calculate_indicator_result(
        actor=admin_user,
        version=version,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        site=site,
        service=service,
        inputs={"value": correction_inputs},
        supersedes=published,
    )
    submit_result_review(actor=admin_user, result=correction)
    publish_indicator_result(actor=approver, result=correction, reason="Corrección trazable")
    published.refresh_from_db()
    correction.refresh_from_db()
    assert published.status == ResultStatus.CORRECTED
    assert published.value == Decimal("80.000000")
    assert correction.status == ResultStatus.PUBLISHED
    assert correction.value == Decimal("60.000000")
    published.value = Decimal("1")
    with pytest.raises(ValidationError, match="inmutable"):
        published.save()
    assert AuditEvent.objects.filter(action="indicator_result.published").count() == 2


def test_result_rejection_and_invalid_calculation_paths(
    admin_user: User,
    organization: Organization,
    area: Area,
    site: Site,
) -> None:
    service = create_service(
        actor=admin_user, site=site, code="SER-KPI", name="Servicio KPI"
    )
    indicator = create_test_indicator(
        admin_user=admin_user, organization=organization, area=area
    )
    approver = create_approver(admin_user=admin_user)
    version = create_effective_version(
        admin_user=admin_user, approver=approver, indicator=indicator
    )
    job = create_import_job(
        admin_user=admin_user,
        organization=organization,
        rows=observation_rows(site=site, service=service),
    )
    observations = materialize_kpi_observations(
        actor=admin_user, job=job, indicator=indicator
    )
    with pytest.raises(ValidationError, match="roles"):
        calculate_indicator_result(
            actor=admin_user,
            version=version,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            inputs={"otro": observations},
        )
    result = calculate_indicator_result(
        actor=admin_user,
        version=version,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        inputs={"value": observations},
    )
    submit_result_review(actor=admin_user, result=result)
    with pytest.raises(ValidationError, match="motivo"):
        reject_indicator_result(actor=approver, result=result, reason="")
    rejected = reject_indicator_result(
        actor=approver, result=result, reason="Revisar fuente sintética"
    )
    assert rejected.status == ResultStatus.REJECTED


def test_protected_models_block_bulk_mutation_and_deletion(
    admin_user: User, organization: Organization, area: Area
) -> None:
    indicator = create_test_indicator(
        admin_user=admin_user, organization=organization, area=area
    )
    with pytest.raises(ValidationError, match="servicios controlados"):
        Indicator.objects.filter(pk=indicator.pk).update(name="Cambio")
    with pytest.raises(ValidationError, match="no se elimina"):
        indicator.delete()
    with pytest.raises(ValidationError, match="no se elimina"):
        Indicator.objects.filter(pk=indicator.pk).delete()
