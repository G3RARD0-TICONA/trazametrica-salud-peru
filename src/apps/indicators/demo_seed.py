from __future__ import annotations

import calendar
import hashlib
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.documents.models import FileAsset, ScanStatus
from apps.imports.models import (
    ImportJob,
    ImportJobStatus,
    ImportTemplateVersion,
    TemplateTargetType,
    TemplateVersionStatus,
)
from apps.organizations.models import Organization, Service
from apps.processes.models import Process

from .formulas import formula_hash, normalize_formula_ast
from .models import (
    Indicator,
    IndicatorDirection,
    IndicatorFrequency,
    IndicatorObservation,
    IndicatorVersion,
    IndicatorVersionStatus,
)

DEMO_NAMESPACE = uuid.UUID("4e91ddac-45f8-51d7-8b2b-ffaf579a00e3")
DEMO_CUTOFF = datetime(2026, 1, 1, tzinfo=UTC)
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def demo_indicator_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


def indicator_formula() -> dict[str, str]:
    return {"op": "average", "role": "value"}


def _demo_approver(actor: User) -> User:
    approver, created = User.objects.get_or_create(
        id=demo_indicator_uuid("user:indicator-approver"),
        defaults={
            "username": "aprobador_indicadores_demo",
            "email": "aprobador.indicadores@example.invalid",
            "first_name": "Aprobador",
            "last_name": "KPI Sintético",
            "created_by": actor,
            "updated_by": actor,
        },
    )
    if created:
        approver.set_unusable_password()
        approver.save(update_fields=["password"])
    return approver


def _indicator_direction(index: int) -> tuple[IndicatorDirection, Decimal, Decimal]:
    if index % 3 == 0:
        return (
            IndicatorDirection.HIGHER_IS_BETTER,
            Decimal("80.000000"),
            Decimal("60.000000"),
        )
    if index % 3 == 1:
        return (
            IndicatorDirection.LOWER_IS_BETTER,
            Decimal("20.000000"),
            Decimal("40.000000"),
        )
    return (
        IndicatorDirection.TARGET_IS_BEST,
        Decimal("50.000000"),
        Decimal("5.000000"),
    )


def _seed_indicator_catalog(
    *, actor: User, organization: Organization, processes: list[Process]
) -> list[Indicator]:
    approver = _demo_approver(actor)
    normalized_formula = normalize_formula_ast(indicator_formula())
    digest = formula_hash(normalized_formula)
    indicators: list[Indicator] = []
    for index in range(200):
        code = f"KPI-{index + 1:03d}"
        process = processes[index % len(processes)]
        indicator, created = Indicator.objects.get_or_create(
            id=demo_indicator_uuid(f"indicator:{code}"),
            defaults={
                "organization": organization,
                "process": process,
                "code": code,
                "name": f"Indicador Administrativo Sintético {index + 1:03d}",
                "owner": actor,
                "created_by": actor,
                "updated_by": actor,
            },
        )
        if not created and (
            indicator.organization_id != organization.pk or indicator.code != code
        ):
            raise ValidationError("La semilla colisiona con un indicador ajeno al dataset.")
        indicators.append(indicator)
        direction, target, warning = _indicator_direction(index)
        version_count = 2 if index < 60 else 1
        for version_no in range(1, version_count + 1):
            is_superseded = version_count == 2 and version_no == 1
            version, version_created = IndicatorVersion.objects.get_or_create(
                id=demo_indicator_uuid(f"indicator-version:{code}:{version_no}"),
                defaults={
                    "indicator": indicator,
                    "version_no": version_no,
                    "status": (
                        IndicatorVersionStatus.SUPERSEDED
                        if is_superseded
                        else IndicatorVersionStatus.EFFECTIVE
                    ),
                    "purpose": f"Medir desempeño administrativo ficticio de {code}.",
                    "unit": "%",
                    "frequency": IndicatorFrequency.MONTHLY,
                    "direction": direction,
                    "formula_ast": normalized_formula,
                    "formula_hash": digest,
                    "target_value": target + Decimal(version_no - 1),
                    "warning_threshold": warning,
                    "valid_from": date(2025 if is_superseded else 2026, 1, 1),
                    "valid_to": date(2025, 12, 31) if is_superseded else None,
                    "submitted_at": DEMO_CUTOFF,
                    "submitted_by": actor,
                    "reviewed_at": DEMO_CUTOFF,
                    "reviewed_by": approver,
                    "approved_at": DEMO_CUTOFF,
                    "approved_by": approver,
                    "decision_reason": "Ficha KPI sintética inicial",
                    "created_by": actor,
                    "updated_by": actor,
                },
            )
            if not version_created and version.formula_hash != digest:
                raise ValidationError("Una fórmula sembrada fue modificada fuera del contrato.")
    return indicators


def _seed_import_job(
    *, actor: User, organization: Organization, observation_count: int
) -> ImportJob:
    template_version = (
        ImportTemplateVersion.objects.select_related("template")
        .filter(
            template__organization=organization,
            template__target_type=TemplateTargetType.KPI_OBSERVATIONS,
            status=TemplateVersionStatus.EFFECTIVE,
        )
        .get()
    )
    file_digest = hashlib.sha256(b"P11-DATOS-SINTETICOS-OBSERVACIONES-V1").hexdigest()
    asset, _ = FileAsset.objects.get_or_create(
        id=demo_indicator_uuid("file:p11-observations-v1"),
        defaults={
            "storage_key": "imports/p11/observaciones-kpi-sinteticas-v1.xlsx",
            "original_name": "observaciones-kpi-sinteticas-v1.xlsx",
            "media_type": XLSX_MEDIA_TYPE,
            "size_bytes": 1,
            "sha256": file_digest,
            "scan_status": ScanStatus.CLEAN,
            "synthetic_confirmed": True,
            "created_by": actor,
            "updated_by": actor,
        },
    )
    job, created = ImportJob.objects.get_or_create(
        id=demo_indicator_uuid("import-job:p11-observations-v1"),
        defaults={
            "template_version": template_version,
            "source_file": asset,
            "organization": organization,
            "status": ImportJobStatus.PROCESSED,
            "file_hash": file_digest,
            "row_count": observation_count,
            "error_count": 0,
            "started_at": DEMO_CUTOFF,
            "finished_at": DEMO_CUTOFF,
            "promoted_at": DEMO_CUTOFF,
            "attempt_count": 1,
            "created_by": actor,
            "updated_by": actor,
        },
    )
    if not created and job.row_count != observation_count:
        raise ValidationError("La cantidad solicitada no coincide con la semilla existente.")
    return job


def _seed_observations(
    *,
    actor: User,
    indicators: list[Indicator],
    services: list[Service],
    job: ImportJob,
    observation_count: int,
) -> None:
    existing = IndicatorObservation.objects.filter(import_job=job).count()
    if existing == observation_count:
        return
    if existing:
        raise ValidationError(
            "La semilla de observaciones está incompleta; requiere restablecimiento."
        )
    batch: list[IndicatorObservation] = []
    for index in range(observation_count):
        indicator = indicators[index % len(indicators)]
        cycle = index // len(indicators)
        service = services[_demo_service_index(cycle, len(services))]
        month = cycle % 12 + 1
        period_start = date(2026, month, 1)
        period_end = date(2026, month, calendar.monthrange(2026, month)[1])
        batch.append(
            IndicatorObservation(
                id=demo_indicator_uuid(f"observation:{index + 1:06d}"),
                indicator=indicator,
                import_job=job,
                site=service.site,
                service=service,
                period_start=period_start,
                period_end=period_end,
                value=(Decimal((index * 37) % 10000) / Decimal(100)).quantize(
                    Decimal("0.000001")
                ),
                dimension_key=f"OBS-SINT-{index + 1:06d}",
                created_by=actor,
                updated_by=actor,
            )
        )
        if len(batch) == 2000:
            IndicatorObservation.objects.bulk_create(batch, batch_size=2000)
            batch.clear()
    if batch:
        IndicatorObservation.objects.bulk_create(batch, batch_size=2000)


def _demo_service_index(cycle: int, service_count: int) -> int:
    """Return a deterministic 80/20 service distribution for synthetic observations.

    Four passes over the service catalog form one 80-position demonstration cycle.  The
    first 80 % of positions rotate through the first 20 % of services; the remaining
    positions cover every other service once.  This creates an explainable Pareto example
    without using or imitating real operational data.
    """

    if service_count < 2:
        return 0
    vital_count = max(1, round(service_count * 0.2))
    cycle_size = service_count * 4
    vital_slots = round(cycle_size * 0.8)
    position = cycle % cycle_size
    if position < vital_slots:
        return position % vital_count
    tail_count = service_count - vital_count
    return vital_count + (position - vital_slots) % tail_count


@transaction.atomic
def seed_indicators(
    *, actor: User, dataset_version: str = "1", observation_count: int = 100_000
) -> dict[str, int]:
    if dataset_version != "1":
        raise ValidationError("La versión de semilla de indicadores no está soportada.")
    if not 1 <= observation_count <= 100_000:
        raise ValidationError("La semilla admite entre 1 y 100 000 observaciones.")
    organization = Organization.objects.filter(is_active=True).get()
    processes = list(
        Process.objects.filter(organization=organization, is_active=True).order_by("code")
    )
    services = list(
        Service.objects.filter(
            site__organization=organization,
            site__is_active=True,
            is_active=True,
        )
        .select_related("site")
        .order_by("code")
    )
    if len(processes) != 100 or len(services) != 20:
        raise ValidationError("Ejecute primero las semillas P07 y P09 completas.")
    indicators = _seed_indicator_catalog(
        actor=actor, organization=organization, processes=processes
    )
    job = _seed_import_job(
        actor=actor, organization=organization, observation_count=observation_count
    )
    _seed_observations(
        actor=actor,
        indicators=indicators,
        services=services,
        job=job,
        observation_count=observation_count,
    )
    return {
        "indicators": Indicator.objects.filter(organization=organization).count(),
        "versions": IndicatorVersion.objects.filter(
            indicator__organization=organization
        ).count(),
        "observations": IndicatorObservation.objects.filter(import_job=job).count(),
    }
