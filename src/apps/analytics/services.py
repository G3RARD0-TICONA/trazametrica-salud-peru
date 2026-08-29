from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max, QuerySet
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.auditlog.models import EventResult
from apps.auditlog.services import record_event
from apps.indicators.models import (
    Indicator,
    IndicatorDirection,
    IndicatorObservation,
    IndicatorVersion,
    IndicatorVersionStatus,
)

from .engine import (
    control_chart,
    descriptive_statistics,
    linear_regression,
    logistic_regression,
    moving_average,
    pareto_analysis,
)
from .models import (
    AnalysisDefinition,
    AnalysisRun,
    AnalysisType,
    DefinitionStatus,
    RunStatus,
)

MAX_ANALYSIS_ROWS = 10_000
PREDICTIVE_TYPES = {AnalysisType.LINEAR_REGRESSION, AnalysisType.LOGISTIC_REGRESSION}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def content_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require(actor: User, capability: Capability) -> None:
    if not actor.is_active or not has_capability(actor, capability):
        raise PermissionDenied("El actor no cuenta con la capacidad analítica requerida.")


def _as_int(value: object) -> int:
    if isinstance(value, (int, str)) and not isinstance(value, bool):
        return int(value)
    raise TypeError("Se esperaba un entero.")


def _as_float(value: object) -> float:
    if isinstance(value, (int, float, str)) and not isinstance(value, bool):
        return float(value)
    raise TypeError("Se esperaba un número.")


def normalize_parameters(analysis_type: str, parameters: Mapping[str, object]) -> dict[str, object]:
    supported = set(AnalysisType.values)
    if analysis_type not in supported:
        raise ValidationError("El tipo de análisis no está soportado.")
    allowed: dict[str, set[str]] = {
        AnalysisType.DESCRIPTIVE: set(),
        AnalysisType.PARETO: set(),
        AnalysisType.CONTROL_CHART: set(),
        AnalysisType.MOVING_AVERAGE: {"window"},
        AnalysisType.LINEAR_REGRESSION: {"test_fraction"},
        AnalysisType.LOGISTIC_REGRESSION: {"test_fraction", "iterations", "learning_rate"},
    }
    unknown = set(parameters) - allowed[analysis_type]
    if unknown:
        raise ValidationError(f"Parámetros no permitidos: {', '.join(sorted(unknown))}.")
    normalized: dict[str, object] = {}
    try:
        if analysis_type == AnalysisType.MOVING_AVERAGE:
            window = _as_int(parameters.get("window", 3))
            if not 2 <= window <= 24:
                raise ValidationError("La ventana debe estar entre 2 y 24.")
            normalized["window"] = window
        if analysis_type in PREDICTIVE_TYPES:
            test_fraction = _as_float(parameters.get("test_fraction", 0.2))
            if not 0.1 <= test_fraction <= 0.4:
                raise ValidationError("La fracción de prueba debe estar entre 0.1 y 0.4.")
            normalized["test_fraction"] = test_fraction
        if analysis_type == AnalysisType.LOGISTIC_REGRESSION:
            iterations = _as_int(parameters.get("iterations", 500))
            learning_rate = _as_float(parameters.get("learning_rate", 0.1))
            if not 50 <= iterations <= 2000 or not 0 < learning_rate <= 0.5:
                raise ValidationError(
                    "Los hiperparámetros logísticos están fuera del rango aprobado."
                )
            normalized.update({"iterations": iterations, "learning_rate": learning_rate})
    except (TypeError, ValueError) as exc:
        raise ValidationError("Los parámetros analíticos no tienen el tipo esperado.") from exc
    return normalized


@transaction.atomic
def create_analysis_definition(
    *,
    actor: User,
    code: str,
    name: str,
    analysis_type: str,
    target_indicator: Indicator,
    parameters: Mapping[str, object] | None = None,
) -> AnalysisDefinition:
    _require(actor, Capability.MANAGE_ANALYTICS)
    if not target_indicator.is_active:
        raise ValidationError("El indicador objetivo debe estar activo.")
    normalized_code = code.strip().upper()
    normalized_parameters = normalize_parameters(analysis_type, parameters or {})
    version_no = (
        int(
            AnalysisDefinition.objects.select_for_update()
            .filter(code__iexact=normalized_code)
            .aggregate(max_no=Max("version_no"))["max_no"]
            or 0
        )
        + 1
    )
    definition = AnalysisDefinition(
        code=normalized_code,
        version_no=version_no,
        name=name.strip(),
        analysis_type=analysis_type,
        target_indicator=target_indicator,
        parameters=normalized_parameters,
        parameters_hash=content_hash(normalized_parameters),
        created_by=actor,
        updated_by=actor,
    )
    definition.full_clean()
    definition.save()
    record_event(
        actor=actor,
        object_type="analytics.AnalysisDefinition",
        object_id=definition.pk,
        action="analysis_definition.created",
        result=EventResult.SUCCESS,
        context={
            "analysis_type": definition.analysis_type,
            "code": definition.code,
            "version_no": definition.version_no,
        },
    )
    return definition


@transaction.atomic
def publish_analysis_definition(
    *, actor: User, definition: AnalysisDefinition
) -> AnalysisDefinition:
    _require(actor, Capability.APPROVE_ANALYTICS)
    locked = AnalysisDefinition.objects.select_for_update().get(pk=definition.pk)
    if locked.status != DefinitionStatus.DRAFT:
        raise ValidationError("Solo una definición en borrador puede publicarse.")
    if locked.created_by_id == actor.pk:
        raise PermissionDenied("El autor no puede publicar su propia definición analítica.")
    normalized_parameters = normalize_parameters(locked.analysis_type, locked.parameters)
    if (
        normalized_parameters != locked.parameters
        or content_hash(locked.parameters) != locked.parameters_hash
    ):
        raise ValidationError("Los parámetros no corresponden al contrato aprobado.")
    prior = AnalysisDefinition.objects.select_for_update().filter(
        code__iexact=locked.code, status=DefinitionStatus.PUBLISHED
    )
    for item in prior:
        item.status = DefinitionStatus.SUPERSEDED
        item.updated_by = actor
        item.full_clean()
        item.save(update_fields=["status", "updated_by", "updated_at"])
    locked.status = DefinitionStatus.PUBLISHED
    locked.published_at = timezone.now()
    locked.published_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "published_at", "published_by", "updated_by", "updated_at"]
    )
    record_event(
        actor=actor,
        object_type="analytics.AnalysisDefinition",
        object_id=locked.pk,
        action="analysis_definition.published",
        result=EventResult.SUCCESS,
        context={"code": locked.code, "parameters_hash": locked.parameters_hash},
    )
    return locked


def _observations(
    definition: AnalysisDefinition, period_start: date | None, period_end: date | None
) -> QuerySet[IndicatorObservation]:
    queryset = IndicatorObservation.objects.filter(
        indicator=definition.target_indicator
    ).select_related("site", "service", "import_job")
    if period_start:
        queryset = queryset.filter(period_end__gte=period_start)
    if period_end:
        queryset = queryset.filter(period_start__lte=period_end)
    return queryset.order_by("period_start", "period_end", "dimension_key", "id")


def _target_version(indicator: Indicator) -> IndicatorVersion:
    version = (
        indicator.versions.filter(
            status__in=[IndicatorVersionStatus.EFFECTIVE, IndicatorVersionStatus.SUPERSEDED],
            target_value__isnull=False,
        )
        .order_by("-version_no")
        .first()
    )
    if version is None:
        raise ValidationError("La regresión logística requiere una meta KPI aprobada.")
    return version


def _binary_label(value: Decimal, version: IndicatorVersion) -> int:
    target = version.target_value
    if target is None:
        raise ValidationError("La regresión logística requiere una meta KPI aprobada.")
    if version.direction == IndicatorDirection.HIGHER_IS_BETTER:
        return int(value >= target)
    if version.direction == IndicatorDirection.LOWER_IS_BETTER:
        return int(value <= target)
    tolerance = version.warning_threshold or Decimal("0")
    return int(abs(value - target) <= tolerance)


def _execute(
    definition: AnalysisDefinition, rows: list[IndicatorObservation]
) -> tuple[dict[str, object], dict[str, object], int, int, bool]:
    values = [float(row.value) for row in rows]
    parameters = definition.parameters
    if definition.analysis_type == AnalysisType.DESCRIPTIVE:
        result = descriptive_statistics(values)
    elif definition.analysis_type == AnalysisType.PARETO:
        result = pareto_analysis(
            [row.service.code if row.service else "SIN-SERVICIO" for row in rows],
            [abs(value) for value in values],
        )
    elif definition.analysis_type == AnalysisType.CONTROL_CHART:
        result = control_chart(values)
    elif definition.analysis_type == AnalysisType.MOVING_AVERAGE:
        result = moving_average(values, window=_as_int(parameters["window"]))
    elif definition.analysis_type == AnalysisType.LINEAR_REGRESSION:
        result = linear_regression(
            list(range(1, len(values) + 1)),
            values,
            test_fraction=_as_float(parameters["test_fraction"]),
        )
    elif definition.analysis_type == AnalysisType.LOGISTIC_REGRESSION:
        version = _target_version(definition.target_indicator)
        result = logistic_regression(
            list(range(1, len(values) + 1)),
            [_binary_label(row.value, version) for row in rows],
            test_fraction=_as_float(parameters["test_fraction"]),
            iterations=_as_int(parameters["iterations"]),
            learning_rate=_as_float(parameters["learning_rate"]),
        )
    else:
        raise ValidationError("El tipo de análisis no está implementado.")
    metrics = result.get("metrics", {})
    normalized_metrics = metrics if isinstance(metrics, dict) else {}
    train_count = _as_int(result.get("train_count", 0))
    test_count = _as_int(result.get("test_count", 0))
    quality_gate = bool(result.get("quality_gate_passed", True))
    return result, normalized_metrics, train_count, test_count, quality_gate


@transaction.atomic
def run_analysis(
    *,
    actor: User,
    definition: AnalysisDefinition,
    period_start: date | None = None,
    period_end: date | None = None,
) -> AnalysisRun:
    _require(actor, Capability.RUN_ANALYTICS)
    if period_start and period_end and period_end < period_start:
        raise ValidationError("El fin del periodo no puede preceder al inicio.")
    locked = (
        AnalysisDefinition.objects.select_for_update()
        .select_related("target_indicator")
        .get(pk=definition.pk)
    )
    if locked.status != DefinitionStatus.PUBLISHED:
        raise ValidationError("Solo una definición publicada puede ejecutarse.")
    rows = list(_observations(locked, period_start, period_end)[: MAX_ANALYSIS_ROWS + 1])
    if not rows:
        raise ValidationError("No existen observaciones sintéticas para el análisis.")
    if len(rows) > MAX_ANALYSIS_ROWS:
        raise ValidationError("El análisis supera el máximo de 10 000 observaciones.")
    input_payload = [
        {
            "id": str(row.pk),
            "period_end": row.period_end.isoformat(),
            "period_start": row.period_start.isoformat(),
            "service_id": str(row.service_id) if row.service_id else None,
            "site_id": str(row.site_id) if row.site_id else None,
            "value": str(row.value),
        }
        for row in rows
    ]
    input_digest = content_hash(input_payload)
    try:
        result, metrics, train_count, test_count, quality_gate = _execute(locked, rows)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    assumptions = {
        "baseline_required": locked.analysis_type in PREDICTIVE_TYPES,
        "chronological_order": True,
        "clinical_decision": False,
        "data_origin": "processed_synthetic_indicator_observations",
        "leakage_control": (
            "chronological_train_test_split"
            if locked.analysis_type in PREDICTIVE_TYPES
            else "not_applicable"
        ),
        "limitations": (
            "Resultado administrativo demostrativo; requiere validación externa antes de uso real."
        ),
    }
    output_digest = content_hash(
        {
            "definition_id": str(locked.pk),
            "input_hash": input_digest,
            "parameters_hash": locked.parameters_hash,
            "result": result,
        }
    )
    run = AnalysisRun(
        definition=locked,
        requested_by=actor,
        period_start=period_start,
        period_end=period_end,
        executed_at=timezone.now(),
        status=RunStatus.COMPLETED if quality_gate else RunStatus.REJECTED_QUALITY,
        input_count=len(rows),
        train_count=train_count,
        test_count=test_count,
        input_hash=input_digest,
        output_hash=output_digest,
        metrics=metrics,
        assumptions=assumptions,
        result=result,
        quality_gate_passed=quality_gate,
        synthetic_confirmed=True,
        created_by=actor,
        updated_by=actor,
    )
    run.full_clean()
    run.save()
    record_event(
        actor=actor,
        object_type="analytics.AnalysisRun",
        object_id=run.pk,
        action="analysis.executed",
        result=EventResult.SUCCESS if quality_gate else EventResult.DENIED,
        reason="" if quality_gate else "El modelo no superó la línea base aprobada.",
        context={
            "analysis_type": locked.analysis_type,
            "definition_code": locked.code,
            "input_count": run.input_count,
            "input_hash": input_digest,
            "output_hash": output_digest,
            "quality_gate_passed": quality_gate,
        },
    )
    return run
