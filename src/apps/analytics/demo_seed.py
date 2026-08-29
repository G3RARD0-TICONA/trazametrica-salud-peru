from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.indicators.models import Indicator

from .models import AnalysisDefinition, AnalysisRun, AnalysisType, DefinitionStatus
from .services import (
    create_analysis_definition,
    publish_analysis_definition,
    run_analysis,
)

DEMO_NAMESPACE = uuid.UUID("25ab1c6d-7d41-5ac4-8685-5024a3a99082")

DEFINITIONS: tuple[tuple[str, str, AnalysisType, dict[str, object]], ...] = (
    ("ANA-DESC-001", "Descriptivos y atípicos KPI", AnalysisType.DESCRIPTIVE, {}),
    ("ANA-PARETO-001", "Pareto administrativo por servicio", AnalysisType.PARETO, {}),
    ("ANA-CONTROL-001", "Gráfico de control KPI", AnalysisType.CONTROL_CHART, {}),
    (
        "ANA-TREND-001",
        "Tendencia y media móvil KPI",
        AnalysisType.MOVING_AVERAGE,
        {"window": 3},
    ),
    (
        "ANA-LINEAR-001",
        "Regresión lineal temporal KPI",
        AnalysisType.LINEAR_REGRESSION,
        {"test_fraction": 0.2},
    ),
    (
        "ANA-LOGISTIC-001",
        "Regresión logística de cumplimiento KPI",
        AnalysisType.LOGISTIC_REGRESSION,
        {"test_fraction": 0.2, "iterations": 500, "learning_rate": 0.1},
    ),
)


def demo_analytics_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


def _approver(actor: User) -> User:
    approver, created = User.objects.get_or_create(
        id=demo_analytics_uuid("user:analytics-approver"),
        defaults={
            "username": "aprobador_analitica_demo",
            "email": "aprobador.analitica@example.invalid",
            "first_name": "Aprobador",
            "last_name": "Analítica Sintética",
            "is_superuser": True,
            "created_by": actor,
            "updated_by": actor,
        },
    )
    if created:
        approver.set_unusable_password()
        approver.save(update_fields=["password"])
    return approver


@transaction.atomic
def seed_analytics(*, actor: User, dataset_version: str = "1") -> dict[str, int]:
    if dataset_version != "1":
        raise ValidationError("La versión de semilla analítica no está soportada.")
    indicators = list(
        Indicator.objects.filter(is_active=True, observations__isnull=False)
        .distinct()
        .order_by("code")[: len(DEFINITIONS)]
    )
    if len(indicators) < len(DEFINITIONS):
        raise ValidationError("Ejecute primero la semilla P11 con observaciones suficientes.")
    approver = _approver(actor)
    definitions: list[AnalysisDefinition] = []
    for indicator, (code, name, analysis_type, parameters) in zip(
        indicators, DEFINITIONS, strict=True
    ):
        definition = AnalysisDefinition.objects.filter(code=code, version_no=1).first()
        if definition is None:
            definition = create_analysis_definition(
                actor=actor,
                code=code,
                name=name,
                analysis_type=analysis_type,
                target_indicator=indicator,
                parameters=parameters,
            )
            definition = publish_analysis_definition(actor=approver, definition=definition)
        elif (
            definition.analysis_type != analysis_type
            or definition.target_indicator_id != indicator.pk
            or definition.status != DefinitionStatus.PUBLISHED
        ):
            raise ValidationError("Una definición analítica sembrada fue modificada.")
        definitions.append(definition)
        if not definition.runs.exists():
            run_analysis(actor=actor, definition=definition)
    return {
        "definitions": len(definitions),
        "runs": AnalysisRun.objects.filter(definition__in=definitions).count(),
        "quality_passed": AnalysisRun.objects.filter(
            definition__in=definitions, quality_gate_passed=True
        ).count(),
    }
