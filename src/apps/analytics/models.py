from __future__ import annotations

import re
import uuid
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.indicators.models import Indicator

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ProtectedAnalyticsQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("La analítica se modifica mediante servicios controlados.")

    def delete(self) -> NoReturn:
        raise ValidationError("La evidencia analítica no se elimina físicamente.")


class AuditedAnalyticsRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_created",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_updated",
    )

    class Meta:
        abstract = True


class AnalysisType(models.TextChoices):
    DESCRIPTIVE = "descriptive", "Descriptivos y atípicos"
    PARETO = "pareto", "Pareto por servicio"
    CONTROL_CHART = "control_chart", "Gráfico de control"
    MOVING_AVERAGE = "moving_average", "Tendencia y media móvil"
    LINEAR_REGRESSION = "linear_regression", "Regresión lineal"
    LOGISTIC_REGRESSION = "logistic_regression", "Regresión logística"


class DefinitionStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    PUBLISHED = "published", "Publicada"
    SUPERSEDED = "superseded", "Sustituida"
    ANNULLED = "annulled", "Anulada"


class RunStatus(models.TextChoices):
    COMPLETED = "completed", "Completada"
    REJECTED_QUALITY = "rejected_quality", "Rechazada por calidad"


class AnalysisDefinition(AuditedAnalyticsRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedAnalyticsQuerySet.as_manager()

    code = models.CharField(max_length=50)
    version_no = models.PositiveIntegerField()
    name = models.CharField(max_length=200)
    analysis_type = models.CharField(max_length=30, choices=AnalysisType.choices)
    target_indicator = models.ForeignKey(
        Indicator, on_delete=models.PROTECT, related_name="analysis_definitions"
    )
    parameters = models.JSONField(blank=True)
    parameters_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20, choices=DefinitionStatus.choices, default=DefinitionStatus.DRAFT
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="analysis_definitions_published",
    )

    class Meta:
        db_table = "analytics_definition"
        ordering = ["code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["code", "version_no"], name="analytics_code_version_uq"
            ),
            models.UniqueConstraint(
                Lower("code"), "version_no", name="analytics_code_version_ci_uq"
            ),
            models.CheckConstraint(condition=Q(version_no__gte=1), name="analytics_version_no_ck"),
            models.CheckConstraint(
                condition=Q(analysis_type__in=AnalysisType.values), name="analytics_type_ck"
            ),
            models.CheckConstraint(
                condition=Q(status__in=DefinitionStatus.values),
                name="analytics_definition_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(parameters_hash__regex=r"^[0-9a-f]{64}$"),
                name="analytics_parameters_hash_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status=DefinitionStatus.PUBLISHED,
                        published_at__isnull=False,
                        published_by__isnull=False,
                    )
                    | (
                        ~Q(status=DefinitionStatus.PUBLISHED)
                        & Q(published_at__isnull=True, published_by__isnull=True)
                    )
                    | Q(
                        status__in=[DefinitionStatus.SUPERSEDED, DefinitionStatus.ANNULLED],
                        published_at__isnull=False,
                        published_by__isnull=False,
                    )
                ),
                name="analytics_publication_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "analysis_type", "code"], name="analytics_catalog_ix")
        ]

    def __str__(self) -> str:
        return f"{self.code} v{self.version_no} ({self.status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            immutable = (
                "code",
                "version_no",
                "name",
                "analysis_type",
                "target_indicator_id",
                "parameters",
                "parameters_hash",
            )
            if original.status != DefinitionStatus.DRAFT and any(
                getattr(original, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError("Una definición analítica publicada es inmutable.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not isinstance(self.parameters, dict):
            raise ValidationError({"parameters": "Los parámetros deben ser un objeto JSON."})
        if not SHA256_PATTERN.fullmatch(self.parameters_hash):
            raise ValidationError({"parameters_hash": "El hash de parámetros no es SHA-256."})
        if not self.target_indicator.is_active:
            raise ValidationError("El indicador objetivo debe estar activo.")

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las definiciones analíticas no se eliminan físicamente.")


class AnalysisRun(AuditedAnalyticsRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedAnalyticsQuerySet.as_manager()

    definition = models.ForeignKey(
        AnalysisDefinition, on_delete=models.PROTECT, related_name="runs"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="analysis_runs_requested",
    )
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    executed_at = models.DateTimeField()
    status = models.CharField(max_length=30, choices=RunStatus.choices)
    input_count = models.PositiveIntegerField()
    train_count = models.PositiveIntegerField(default=0)
    test_count = models.PositiveIntegerField(default=0)
    input_hash = models.CharField(max_length=64)
    output_hash = models.CharField(max_length=64)
    metrics = models.JSONField(blank=True)
    assumptions = models.JSONField()
    result = models.JSONField()
    quality_gate_passed = models.BooleanField()
    synthetic_confirmed = models.BooleanField(default=True)

    class Meta:
        db_table = "analytics_run"
        ordering = ["-executed_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=RunStatus.values), name="analytics_run_status_ck"
            ),
            models.CheckConstraint(
                condition=Q(input_count__gte=1), name="analytics_run_input_count_ck"
            ),
            models.CheckConstraint(
                condition=Q(period_end__isnull=True) | Q(period_end__gte=F("period_start")),
                name="analytics_run_dates_ck",
            ),
            models.CheckConstraint(
                condition=Q(input_hash__regex=r"^[0-9a-f]{64}$"), name="analytics_input_hash_ck"
            ),
            models.CheckConstraint(
                condition=Q(output_hash__regex=r"^[0-9a-f]{64}$"), name="analytics_output_hash_ck"
            ),
            models.CheckConstraint(
                condition=Q(synthetic_confirmed=True), name="analytics_synthetic_ck"
            ),
            models.CheckConstraint(
                condition=(
                    Q(status=RunStatus.COMPLETED, quality_gate_passed=True)
                    | Q(status=RunStatus.REJECTED_QUALITY, quality_gate_passed=False)
                ),
                name="analytics_quality_status_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["definition", "-executed_at"], name="analytics_run_history_ix")
        ]

    def __str__(self) -> str:
        return f"{self.definition.code}: {self.executed_at.isoformat()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValidationError("Una ejecución analítica es inmutable.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError("El fin del periodo no puede preceder al inicio.")
        if self.definition.status != DefinitionStatus.PUBLISHED:
            raise ValidationError("La ejecución requiere una definición publicada.")
        if self.requested_by_id != self.created_by_id:
            raise ValidationError("El solicitante debe corresponder al autor de la ejecución.")
        if not all(
            isinstance(value, dict) for value in (self.metrics, self.assumptions, self.result)
        ):
            raise ValidationError("Métricas, supuestos y resultado deben ser objetos JSON.")
        if not SHA256_PATTERN.fullmatch(self.input_hash) or not SHA256_PATTERN.fullmatch(
            self.output_hash
        ):
            raise ValidationError("Los hashes analíticos deben ser SHA-256.")

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las ejecuciones analíticas no se eliminan físicamente.")
