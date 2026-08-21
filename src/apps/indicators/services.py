from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.accounts.services import date_ranges_overlap
from apps.auditlog.models import EventResult
from apps.auditlog.services import record_event
from apps.imports.models import ImportJob, ImportJobStatus, ImportRow, TemplateTargetType
from apps.organizations.models import Organization, Service, Site
from apps.processes.models import Process

from .formulas import evaluate_formula, formula_hash, formula_roles, normalize_formula_ast
from .models import (
    Indicator,
    IndicatorDirection,
    IndicatorFrequency,
    IndicatorObservation,
    IndicatorResult,
    IndicatorVersion,
    IndicatorVersionStatus,
    PerformanceStatus,
    ResultInput,
    ResultStatus,
)


def _require(actor: User, capability: Capability) -> None:
    if not actor.is_active or not has_capability(actor, capability):
        raise PermissionDenied("El actor no cuenta con la capacidad de indicadores requerida.")


def _require_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized:
        raise ValidationError("La decisión requiere un motivo.")
    return normalized


def _performance_status(version: IndicatorVersion, value: Decimal) -> PerformanceStatus:
    target = version.target_value
    warning = version.warning_threshold
    if target is None:
        return PerformanceStatus.NOT_EVALUATED
    if version.direction == IndicatorDirection.HIGHER_IS_BETTER:
        if value >= target:
            return PerformanceStatus.ON_TARGET
        if warning is not None and value >= warning:
            return PerformanceStatus.WARNING
        return PerformanceStatus.OFF_TARGET
    if version.direction == IndicatorDirection.LOWER_IS_BETTER:
        if value <= target:
            return PerformanceStatus.ON_TARGET
        if warning is not None and value <= warning:
            return PerformanceStatus.WARNING
        return PerformanceStatus.OFF_TARGET
    if value == target:
        return PerformanceStatus.ON_TARGET
    if warning is not None and abs(value - target) <= warning:
        return PerformanceStatus.WARNING
    return PerformanceStatus.OFF_TARGET


@transaction.atomic
def create_indicator(
    *,
    actor: User,
    organization: Organization,
    process: Process,
    code: str,
    name: str,
    owner: User,
) -> Indicator:
    _require(actor, Capability.DRAFT_INDICATORS)
    if not organization.is_active or not process.is_active or not owner.is_active:
        raise ValidationError("Organización, proceso y responsable deben estar activos.")
    indicator = Indicator(
        organization=organization,
        process=process,
        code=code,
        name=name,
        owner=owner,
        created_by=actor,
        updated_by=actor,
    )
    indicator.full_clean()
    indicator.save()
    record_event(
        actor=actor,
        object_type="indicators.Indicator",
        object_id=indicator.pk,
        action="indicator.created",
        result=EventResult.SUCCESS,
        context={"code": indicator.code, "process_id": str(process.pk)},
    )
    return indicator


@transaction.atomic
def create_indicator_version(
    *,
    actor: User,
    indicator: Indicator,
    purpose: str,
    unit: str,
    frequency: IndicatorFrequency,
    direction: IndicatorDirection,
    formula_ast: object,
    target_value: Decimal | None,
    warning_threshold: Decimal | None,
) -> IndicatorVersion:
    _require(actor, Capability.DRAFT_INDICATORS)
    locked_indicator = Indicator.objects.select_for_update().get(pk=indicator.pk)
    if not locked_indicator.is_active:
        raise ValidationError("El indicador debe estar activo.")
    normalized_formula = normalize_formula_ast(formula_ast)
    version_no = int(
        locked_indicator.versions.aggregate(max_no=Max("version_no"))["max_no"] or 0
    ) + 1
    version = IndicatorVersion(
        indicator=locked_indicator,
        version_no=version_no,
        status=IndicatorVersionStatus.DRAFT,
        purpose=purpose,
        unit=unit,
        frequency=frequency,
        direction=direction,
        formula_ast=normalized_formula,
        formula_hash=formula_hash(normalized_formula),
        target_value=target_value,
        warning_threshold=warning_threshold,
        created_by=actor,
        updated_by=actor,
    )
    version.full_clean()
    version.save()
    record_event(
        actor=actor,
        object_type="indicators.IndicatorVersion",
        object_id=version.pk,
        action="indicator_version.created",
        result=EventResult.SUCCESS,
        context={"indicator_id": str(indicator.pk), "version_no": version_no},
    )
    return version


@transaction.atomic
def update_indicator_draft(
    *,
    actor: User,
    version: IndicatorVersion,
    purpose: str,
    unit: str,
    frequency: IndicatorFrequency,
    direction: IndicatorDirection,
    formula_ast: object,
    target_value: Decimal | None,
    warning_threshold: Decimal | None,
) -> IndicatorVersion:
    _require(actor, Capability.DRAFT_INDICATORS)
    locked = IndicatorVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != IndicatorVersionStatus.DRAFT:
        raise ValidationError("Solo una ficha en borrador puede editarse.")
    normalized_formula = normalize_formula_ast(formula_ast)
    locked.purpose = purpose
    locked.unit = unit
    locked.frequency = frequency
    locked.direction = direction
    locked.formula_ast = normalized_formula
    locked.formula_hash = formula_hash(normalized_formula)
    locked.target_value = target_value
    locked.warning_threshold = warning_threshold
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "purpose",
            "unit",
            "frequency",
            "direction",
            "formula_ast",
            "formula_hash",
            "target_value",
            "warning_threshold",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="indicators.IndicatorVersion",
        object_id=locked.pk,
        action="indicator_version.updated",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def submit_indicator_version(*, actor: User, version: IndicatorVersion) -> IndicatorVersion:
    _require(actor, Capability.DRAFT_INDICATORS)
    locked = IndicatorVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != IndicatorVersionStatus.DRAFT:
        raise ValidationError("Solo una ficha en borrador puede enviarse a revisión.")
    normalized_formula = normalize_formula_ast(locked.formula_ast)
    if not formula_roles(normalized_formula):
        raise ValidationError("La fórmula debe utilizar al menos un rol de observaciones.")
    if formula_hash(normalized_formula) != locked.formula_hash:
        raise ValidationError("El hash de la fórmula no coincide con su contenido.")
    locked.status = IndicatorVersionStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.decision_reason = ""
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "submitted_at",
            "submitted_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="indicators.IndicatorVersion",
        object_id=locked.pk,
        action="indicator_version.submitted",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def reject_indicator_version(
    *, actor: User, version: IndicatorVersion, reason: str
) -> IndicatorVersion:
    _require(actor, Capability.REVIEW_INDICATORS)
    normalized_reason = _require_reason(reason)
    locked = IndicatorVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != IndicatorVersionStatus.IN_REVIEW:
        raise ValidationError("Solo una ficha en revisión puede rechazarse.")
    locked.status = IndicatorVersionStatus.DRAFT
    locked.reviewed_at = timezone.now()
    locked.reviewed_by = actor
    locked.decision_reason = normalized_reason
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "reviewed_at",
            "reviewed_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="indicators.IndicatorVersion",
        object_id=locked.pk,
        action="indicator_version.rejected",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"version_no": locked.version_no},
    )
    return locked


def _supersede_indicator_versions(
    *, actor: User, version: IndicatorVersion, valid_from: date, valid_to: date | None
) -> None:
    candidates = (
        IndicatorVersion.objects.select_for_update()
        .filter(
            indicator=version.indicator,
            status__in=[IndicatorVersionStatus.APPROVED, IndicatorVersionStatus.EFFECTIVE],
        )
        .exclude(pk=version.pk)
    )
    for other in candidates:
        if other.valid_from is None:
            raise ValidationError("La ficha aprobada existente carece de inicio de vigencia.")
        if not date_ranges_overlap(other.valid_from, other.valid_to, valid_from, valid_to):
            continue
        if other.status == IndicatorVersionStatus.EFFECTIVE and other.valid_from < valid_from:
            other.valid_to = valid_from - timedelta(days=1)
            if valid_from <= timezone.localdate():
                other.status = IndicatorVersionStatus.SUPERSEDED
            other.updated_by = actor
            other.save(update_fields=["valid_to", "status", "updated_by", "updated_at"])
            continue
        raise ValidationError("La vigencia propuesta se superpone con otra ficha aprobada.")


@transaction.atomic
def approve_indicator_version(
    *,
    actor: User,
    version: IndicatorVersion,
    valid_from: date,
    valid_to: date | None = None,
    reason: str = "",
) -> IndicatorVersion:
    _require(actor, Capability.PUBLISH_INDICATORS)
    locked = IndicatorVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != IndicatorVersionStatus.IN_REVIEW:
        raise ValidationError("Solo una ficha en revisión puede aprobarse.")
    if locked.created_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propia ficha KPI.")
    if valid_to is not None and valid_to < valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")
    if formula_hash(normalize_formula_ast(locked.formula_ast)) != locked.formula_hash:
        raise ValidationError("La fórmula cambió después de su envío.")
    _supersede_indicator_versions(
        actor=actor, version=locked, valid_from=valid_from, valid_to=valid_to
    )
    locked.status = (
        IndicatorVersionStatus.EFFECTIVE
        if valid_from <= timezone.localdate()
        else IndicatorVersionStatus.APPROVED
    )
    locked.valid_from = valid_from
    locked.valid_to = valid_to
    locked.reviewed_at = timezone.now()
    locked.reviewed_by = actor
    locked.approved_at = locked.reviewed_at
    locked.approved_by = actor
    locked.decision_reason = reason.strip()
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "valid_from",
            "valid_to",
            "reviewed_at",
            "reviewed_by",
            "approved_at",
            "approved_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="indicators.IndicatorVersion",
        object_id=locked.pk,
        action="indicator_version.approved",
        result=EventResult.SUCCESS,
        reason=locked.decision_reason,
        context={"status": locked.status, "version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def deactivate_indicator(*, actor: User, indicator: Indicator, reason: str) -> Indicator:
    _require(actor, Capability.DRAFT_INDICATORS)
    normalized_reason = _require_reason(reason)
    locked = Indicator.objects.select_for_update().get(pk=indicator.pk)
    if not locked.is_active:
        raise ValidationError("El indicador ya está inactivo.")
    if locked.versions.filter(status=IndicatorVersionStatus.IN_REVIEW).exists():
        raise ValidationError("No se desactiva un indicador con una ficha en revisión.")
    locked.is_active = False
    locked.deactivated_at = timezone.now()
    locked.deactivated_by = actor
    locked.deactivation_reason = normalized_reason
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "is_active",
            "deactivated_at",
            "deactivated_by",
            "deactivation_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="indicators.Indicator",
        object_id=locked.pk,
        action="indicator.deactivated",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"code": locked.code},
    )
    return locked


def _parse_observation_row(
    *,
    actor: User,
    row: ImportRow,
    indicator: Indicator,
    sites: dict[str, Site],
    services: dict[tuple[str, str], Service],
) -> IndicatorObservation:
    data = row.raw_data
    try:
        site_code = str(data["site_code"]).strip().upper()
        service_code = str(data["service_code"]).strip().upper()
        period_start = date.fromisoformat(str(data["period_start"]))
        period_end = date.fromisoformat(str(data["period_end"]))
        value = Decimal(str(data["value"]))
        dimension_key = str(data["dimension_key"]).strip()
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        raise ValidationError(f"La fila {row.row_number} no cumple el contrato KPI.") from exc
    site = sites.get(site_code)
    service = services.get((site_code, service_code))
    if site is None or service is None:
        raise ValidationError(f"La fila {row.row_number} contiene sede o servicio desconocido.")
    observation = IndicatorObservation(
        indicator=indicator,
        import_job=row.import_job,
        site=site,
        service=service,
        period_start=period_start,
        period_end=period_end,
        value=value,
        dimension_key=dimension_key,
        source_row=row,
        created_by=actor,
        updated_by=actor,
    )
    observation.full_clean()
    return observation


@transaction.atomic
def materialize_kpi_observations(
    *, actor: User, job: ImportJob, indicator: Indicator
) -> list[IndicatorObservation]:
    _require(actor, Capability.DRAFT_INDICATORS)
    locked_job = (
        ImportJob.objects.select_for_update()
        .select_related("template_version__template")
        .get(pk=job.pk)
    )
    locked_indicator = Indicator.objects.select_for_update().get(pk=indicator.pk)
    if locked_job.status != ImportJobStatus.PROCESSED:
        raise ValidationError("La carga debe estar procesada antes de crear observaciones.")
    if locked_job.template_version.template.target_type != TemplateTargetType.KPI_OBSERVATIONS:
        raise ValidationError("La carga no utiliza la plantilla de observaciones KPI.")
    if locked_job.organization_id != locked_indicator.organization_id:
        raise ValidationError("La carga y el indicador pertenecen a ámbitos diferentes.")
    if locked_job.indicator_observations.exists():
        raise ValidationError("La carga ya fue materializada como observaciones KPI.")
    rows = list(locked_job.rows.select_for_update().filter(is_valid=True).order_by("row_number"))
    if len(rows) != locked_job.row_count or locked_job.error_count:
        raise ValidationError("La carga procesada no conserva todas sus filas válidas.")
    sites = {
        site.code: site
        for site in Site.objects.filter(
            organization=locked_indicator.organization, is_active=True
        )
    }
    services = {
        (service.site.code, service.code): service
        for service in Service.objects.filter(
            site__organization=locked_indicator.organization,
            site__is_active=True,
            is_active=True,
        ).select_related("site")
    }
    observations = [
        _parse_observation_row(
            actor=actor,
            row=row,
            indicator=locked_indicator,
            sites=sites,
            services=services,
        )
        for row in rows
    ]
    IndicatorObservation.objects.bulk_create(observations, batch_size=1000)
    record_event(
        actor=actor,
        object_type="indicators.Indicator",
        object_id=locked_indicator.pk,
        action="indicator_observations.materialized",
        result=EventResult.SUCCESS,
        context={"import_job_id": str(job.pk), "row_count": len(observations)},
    )
    return observations


def _result_hash(
    *,
    version: IndicatorVersion,
    period_start: date,
    period_end: date,
    site: Site | None,
    service: Service | None,
    value: Decimal,
    inputs: Mapping[str, Sequence[IndicatorObservation]],
    supersedes: IndicatorResult | None,
) -> str:
    payload = {
        "formula_hash": version.formula_hash,
        "indicator_version_id": str(version.pk),
        "inputs": [
            {
                "observation_id": str(observation.pk),
                "position": position,
                "role": role,
                "value": str(observation.value),
            }
            for role in sorted(inputs)
            for position, observation in enumerate(inputs[role], start=1)
        ],
        "period_end": period_end.isoformat(),
        "period_start": period_start.isoformat(),
        "service_id": str(service.pk) if service else None,
        "site_id": str(site.pk) if site else None,
        "supersedes_id": str(supersedes.pk) if supersedes else None,
        "value": str(value),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def _validate_result_scope(
    *,
    version: IndicatorVersion,
    period_start: date,
    period_end: date,
    site: Site | None,
    service: Service | None,
    observations: Sequence[IndicatorObservation],
) -> None:
    if period_end < period_start:
        raise ValidationError("El fin del periodo no puede preceder al inicio.")
    if version.status not in {
        IndicatorVersionStatus.EFFECTIVE,
        IndicatorVersionStatus.SUPERSEDED,
    }:
        raise ValidationError("La fórmula debe estar aprobada y vigente para el periodo.")
    if (
        version.valid_from is None
        or period_start < version.valid_from
        or (version.valid_to is not None and period_end > version.valid_to)
    ):
        raise ValidationError("La versión de fórmula no cubre el periodo calculado.")
    organization_id = version.indicator.organization_id
    if site is not None and site.organization_id != organization_id:
        raise ValidationError("La sede no pertenece al indicador.")
    if service is not None and (site is None or service.site_id != site.pk):
        raise ValidationError("El servicio no pertenece a la sede seleccionada.")
    for observation in observations:
        if observation.indicator_id != version.indicator_id:
            raise ValidationError("Una observación pertenece a otro indicador.")
        if observation.period_start < period_start or observation.period_end > period_end:
            raise ValidationError("Una observación está fuera del periodo calculado.")
        if site is not None and observation.site_id != site.pk:
            raise ValidationError("Una observación pertenece a otra sede.")
        if service is not None and observation.service_id != service.pk:
            raise ValidationError("Una observación pertenece a otro servicio.")


@transaction.atomic
def calculate_indicator_result(
    *,
    actor: User,
    version: IndicatorVersion,
    period_start: date,
    period_end: date,
    inputs: Mapping[str, Sequence[IndicatorObservation]],
    site: Site | None = None,
    service: Service | None = None,
    supersedes: IndicatorResult | None = None,
) -> IndicatorResult:
    _require(actor, Capability.DRAFT_INDICATORS)
    locked_version = (
        IndicatorVersion.objects.select_for_update()
        .select_related("indicator")
        .get(pk=version.pk)
    )
    normalized_formula = normalize_formula_ast(locked_version.formula_ast)
    if formula_hash(normalized_formula) != locked_version.formula_hash:
        raise ValidationError("La fórmula almacenada no coincide con su hash aprobado.")
    expected_roles = formula_roles(normalized_formula)
    normalized_inputs = {str(role).casefold(): list(values) for role, values in inputs.items()}
    if set(normalized_inputs) != set(expected_roles):
        raise ValidationError("Los roles de observación no coinciden con la fórmula.")
    all_observations = [item for values in normalized_inputs.values() for item in values]
    observation_ids = [item.pk for item in all_observations]
    if len(observation_ids) != len(set(observation_ids)):
        raise ValidationError("Una observación no puede utilizarse más de una vez.")
    locked_observations = {
        item.pk: item
        # PostgreSQL no permite bloquear el lado anulable de los LEFT JOIN
        # generados por site/service. El bloqueo se limita explícitamente a la
        # fila de observación; las relaciones se cargan solo para validar el
        # alcance sin intentar bloquearlas.
        for item in IndicatorObservation.objects.select_for_update(of=("self",))
        .select_related("indicator", "site", "service")
        .filter(pk__in=observation_ids)
    }
    if len(locked_observations) != len(observation_ids):
        raise ValidationError("Una o más observaciones no existen.")
    normalized_inputs = {
        role: [locked_observations[item.pk] for item in values]
        for role, values in normalized_inputs.items()
    }
    all_observations = [item for values in normalized_inputs.values() for item in values]
    _validate_result_scope(
        version=locked_version,
        period_start=period_start,
        period_end=period_end,
        site=site,
        service=service,
        observations=all_observations,
    )
    locked_supersedes = None
    if supersedes is not None:
        locked_supersedes = IndicatorResult.objects.select_for_update().get(pk=supersedes.pk)
        if locked_supersedes.status != ResultStatus.PUBLISHED:
            raise ValidationError("Solo un resultado publicado admite corrección.")
    value = evaluate_formula(
        normalized_formula,
        {role: [item.value for item in values] for role, values in normalized_inputs.items()},
    )
    digest = _result_hash(
        version=locked_version,
        period_start=period_start,
        period_end=period_end,
        site=site,
        service=service,
        value=value,
        inputs=normalized_inputs,
        supersedes=locked_supersedes,
    )
    result = IndicatorResult(
        indicator_version=locked_version,
        site=site,
        service=service,
        period_start=period_start,
        period_end=period_end,
        value=value,
        performance_status=_performance_status(locked_version, value),
        status=ResultStatus.CALCULATED,
        calculated_at=timezone.now(),
        calculated_by=actor,
        result_hash=digest,
        supersedes=locked_supersedes,
        created_by=actor,
        updated_by=actor,
    )
    result.full_clean()
    result.save()
    input_rows = [
        ResultInput(
            result=result,
            observation=observation,
            input_role=role,
            position=position,
        )
        for role in sorted(normalized_inputs)
        for position, observation in enumerate(normalized_inputs[role], start=1)
    ]
    for input_row in input_rows:
        input_row.full_clean()
    ResultInput.objects.bulk_create(input_rows, batch_size=1000)
    record_event(
        actor=actor,
        object_type="indicators.IndicatorResult",
        object_id=result.pk,
        action="indicator_result.calculated",
        result=EventResult.SUCCESS,
        context={
            "formula_hash": locked_version.formula_hash,
            "input_count": len(input_rows),
            "result_hash": digest,
        },
    )
    return result


@transaction.atomic
def submit_result_review(*, actor: User, result: IndicatorResult) -> IndicatorResult:
    _require(actor, Capability.REVIEW_INDICATORS)
    locked = IndicatorResult.objects.select_for_update().get(pk=result.pk)
    if locked.status != ResultStatus.CALCULATED:
        raise ValidationError("Solo un resultado calculado puede enviarse a revisión.")
    locked.status = ResultStatus.IN_REVIEW
    locked.reviewed_at = timezone.now()
    locked.reviewed_by = actor
    locked.decision_reason = ""
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "reviewed_at",
            "reviewed_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="indicators.IndicatorResult",
        object_id=locked.pk,
        action="indicator_result.submitted",
        result=EventResult.SUCCESS,
        context={"result_hash": locked.result_hash},
    )
    return locked


@transaction.atomic
def reject_indicator_result(
    *, actor: User, result: IndicatorResult, reason: str
) -> IndicatorResult:
    _require(actor, Capability.PUBLISH_INDICATORS)
    normalized_reason = _require_reason(reason)
    locked = IndicatorResult.objects.select_for_update().get(pk=result.pk)
    if locked.status != ResultStatus.IN_REVIEW:
        raise ValidationError("Solo un resultado en revisión puede rechazarse.")
    if locked.calculated_by_id == actor.pk:
        raise PermissionDenied("El calculador no puede decidir sobre su propio resultado.")
    locked.status = ResultStatus.REJECTED
    locked.reviewed_at = timezone.now()
    locked.reviewed_by = actor
    locked.decision_reason = normalized_reason
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "reviewed_at",
            "reviewed_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="indicators.IndicatorResult",
        object_id=locked.pk,
        action="indicator_result.rejected",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"result_hash": locked.result_hash},
    )
    return locked


@transaction.atomic
def publish_indicator_result(
    *, actor: User, result: IndicatorResult, reason: str = ""
) -> IndicatorResult:
    _require(actor, Capability.PUBLISH_INDICATORS)
    locked = (
        # supersedes es anulable; PostgreSQL solo debe bloquear el resultado
        # que se publica, no el lado opcional del LEFT JOIN.
        IndicatorResult.objects.select_for_update(of=("self",))
        .select_related("indicator_version__indicator", "supersedes")
        .get(pk=result.pk)
    )
    if locked.status != ResultStatus.IN_REVIEW:
        raise ValidationError("Solo un resultado en revisión puede publicarse.")
    if locked.calculated_by_id == actor.pk:
        raise PermissionDenied("El calculador no puede publicar su propio resultado.")
    current = (
        IndicatorResult.objects.select_for_update()
        .filter(
            indicator_version__indicator=locked.indicator_version.indicator,
            period_start=locked.period_start,
            period_end=locked.period_end,
            site=locked.site,
            service=locked.service,
            status=ResultStatus.PUBLISHED,
        )
        .exclude(pk=locked.pk)
        .first()
    )
    if locked.supersedes_id is None and current is not None:
        raise ValidationError("Ya existe un resultado publicado para el mismo ámbito y periodo.")
    if locked.supersedes_id is not None:
        previous = IndicatorResult.objects.select_for_update().get(pk=locked.supersedes_id)
        if previous.status != ResultStatus.PUBLISHED or current != previous:
            raise ValidationError("La corrección no sustituye el resultado publicado vigente.")
        previous.status = ResultStatus.CORRECTED
        previous.updated_by = actor
        previous.save(update_fields=["status", "updated_by", "updated_at"])
    locked.status = ResultStatus.PUBLISHED
    locked.published_at = timezone.now()
    locked.published_by = actor
    locked.reviewed_at = locked.published_at
    locked.reviewed_by = actor
    locked.decision_reason = reason.strip()
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "published_at",
            "published_by",
            "reviewed_at",
            "reviewed_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="indicators.IndicatorResult",
        object_id=locked.pk,
        action="indicator_result.published",
        result=EventResult.SUCCESS,
        reason=locked.decision_reason,
        context={
            "performance_status": locked.performance_status,
            "result_hash": locked.result_hash,
            "supersedes_id": str(locked.supersedes_id) if locked.supersedes_id else None,
        },
    )
    return locked
