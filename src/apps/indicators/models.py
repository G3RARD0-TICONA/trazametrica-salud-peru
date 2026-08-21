from __future__ import annotations

import re
import uuid
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.imports.models import ImportJob, ImportJobStatus, ImportRow, TemplateTargetType
from apps.organizations.models import Organization, Service, Site
from apps.processes.models import Process

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ProtectedIndicatorQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los indicadores se modifican mediante servicios controlados.")

    def delete(self) -> NoReturn:
        raise ValidationError("La evidencia de indicadores no se elimina físicamente.")


class AuditedIndicatorRecord(models.Model):
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


class IndicatorVersionStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    APPROVED = "approved", "Aprobada"
    EFFECTIVE = "effective", "Vigente"
    SUPERSEDED = "superseded", "Sustituida"
    ANNULLED = "annulled", "Anulada"


class IndicatorFrequency(models.TextChoices):
    DAILY = "daily", "Diaria"
    WEEKLY = "weekly", "Semanal"
    MONTHLY = "monthly", "Mensual"
    QUARTERLY = "quarterly", "Trimestral"
    ANNUAL = "annual", "Anual"


class IndicatorDirection(models.TextChoices):
    HIGHER_IS_BETTER = "higher_is_better", "Mayor es mejor"
    LOWER_IS_BETTER = "lower_is_better", "Menor es mejor"
    TARGET_IS_BEST = "target_is_best", "Objetivo exacto"


class ResultStatus(models.TextChoices):
    CALCULATED = "calculated", "Calculado"
    IN_REVIEW = "in_review", "En revisión"
    REJECTED = "rejected", "Rechazado"
    PUBLISHED = "published", "Publicado"
    CORRECTED = "corrected", "Corregido"


class PerformanceStatus(models.TextChoices):
    ON_TARGET = "on_target", "En meta"
    WARNING = "warning", "Advertencia"
    OFF_TARGET = "off_target", "Fuera de meta"
    NOT_EVALUATED = "not_evaluated", "Sin evaluación"


INDICATOR_LIFECYCLE_CONDITION = Q(
    is_active=True,
    deactivated_at__isnull=True,
    deactivated_by__isnull=True,
    deactivation_reason="",
) | (
    Q(is_active=False, deactivated_at__isnull=False, deactivated_by__isnull=False)
    & ~Q(deactivation_reason="")
)


class Indicator(AuditedIndicatorRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedIndicatorQuerySet.as_manager()

    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="indicators"
    )
    process = models.ForeignKey(Process, on_delete=models.PROTECT, related_name="indicators")
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_indicators",
    )
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicators_deactivated",
    )
    deactivation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "indicators_indicator"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"), Lower("code"), name="indicator_scope_code_ci_uq"
            ),
            models.CheckConstraint(
                condition=INDICATOR_LIFECYCLE_CONDITION,
                name="indicator_lifecycle_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name=""), name="indicator_text_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "process", "is_active", "code"],
                name="indicator_catalog_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.process.organization_id != self.organization_id:
            raise ValidationError("El proceso y el indicador deben pertenecer a la organización.")
        if not self.owner.is_active:
            raise ValidationError("El responsable del indicador debe estar activo.")

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los indicadores no se eliminan físicamente.")


class IndicatorVersion(AuditedIndicatorRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedIndicatorQuerySet.as_manager()

    indicator = models.ForeignKey(Indicator, on_delete=models.PROTECT, related_name="versions")
    version_no = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=IndicatorVersionStatus.choices)
    purpose = models.TextField()
    unit = models.CharField(max_length=30)
    frequency = models.CharField(max_length=20, choices=IndicatorFrequency.choices)
    direction = models.CharField(max_length=30, choices=IndicatorDirection.choices)
    formula_ast = models.JSONField()
    formula_hash = models.CharField(max_length=64)
    target_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    warning_threshold = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicator_versions_submitted",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicator_versions_reviewed",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicator_versions_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "indicators_indicator_version"
        ordering = ["indicator__code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["indicator", "version_no"], name="indicator_version_no_uq"
            ),
            models.CheckConstraint(
                condition=Q(version_no__gte=1), name="indicator_version_no_ck"
            ),
            models.CheckConstraint(
                condition=Q(status__in=IndicatorVersionStatus.values),
                name="indicator_version_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(formula_hash__regex=r"^[0-9a-f]{64}$"),
                name="indicator_formula_hash_ck",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="indicator_version_dates_ck",
            ),
            models.CheckConstraint(
                condition=~Q(purpose="") & ~Q(unit=""), name="indicator_version_text_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=["indicator", "status", "-version_no"],
                name="indicator_version_state_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.indicator.code} v{self.version_no} ({self.status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.purpose = self.purpose.strip()
        self.unit = self.unit.strip()
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            immutable = (
                "indicator_id",
                "version_no",
                "purpose",
                "unit",
                "frequency",
                "direction",
                "formula_ast",
                "formula_hash",
                "target_value",
                "warning_threshold",
            )
            if original.status != IndicatorVersionStatus.DRAFT and any(
                getattr(original, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError("Una ficha enviada o aprobada es inmutable.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not SHA256_PATTERN.fullmatch(self.formula_hash):
            raise ValidationError({"formula_hash": "El hash de fórmula no es SHA-256."})
        if not isinstance(self.formula_ast, dict):
            raise ValidationError({"formula_ast": "La fórmula debe ser declarativa."})
        if self.warning_threshold is not None and self.target_value is None:
            raise ValidationError("Un umbral de advertencia requiere una meta.")
        if self.warning_threshold is not None and self.target_value is not None:
            if (
                self.direction == IndicatorDirection.HIGHER_IS_BETTER
                and self.warning_threshold > self.target_value
            ):
                raise ValidationError("Para mayor es mejor, el umbral no supera la meta.")
            if (
                self.direction == IndicatorDirection.LOWER_IS_BETTER
                and self.warning_threshold < self.target_value
            ):
                raise ValidationError("Para menor es mejor, el umbral no es menor que la meta.")
            if (
                self.direction == IndicatorDirection.TARGET_IS_BEST
                and self.warning_threshold < 0
            ):
                raise ValidationError("La tolerancia del objetivo exacto no puede ser negativa.")

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las versiones de indicador no se eliminan físicamente.")


class IndicatorObservation(AuditedIndicatorRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedIndicatorQuerySet.as_manager()

    indicator = models.ForeignKey(
        Indicator, on_delete=models.PROTECT, related_name="observations"
    )
    import_job = models.ForeignKey(
        ImportJob, on_delete=models.PROTECT, related_name="indicator_observations"
    )
    site = models.ForeignKey(
        Site, null=True, blank=True, on_delete=models.PROTECT, related_name="indicator_observations"
    )
    service = models.ForeignKey(
        Service,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicator_observations",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    value = models.DecimalField(max_digits=20, decimal_places=6)
    dimension_key = models.CharField(max_length=200)
    source_row = models.OneToOneField(
        ImportRow,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicator_observation",
    )

    class Meta:
        db_table = "indicators_observation"
        ordering = ["indicator__code", "period_start", "dimension_key"]
        constraints = [
            models.CheckConstraint(
                condition=Q(period_end__gte=F("period_start")),
                name="indicator_observation_dates_ck",
            ),
            models.CheckConstraint(
                condition=~Q(dimension_key=""), name="indicator_observation_dimension_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=["indicator", "period_start", "period_end"],
                name="indicator_obs_period_ix",
            ),
            models.Index(
                fields=["site", "service", "period_start"],
                name="indicator_observation_scope_ix",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.indicator.code} {self.period_start}: {self.value}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.dimension_key = self.dimension_key.strip()
        if not self._state.adding:
            raise ValidationError("Una observación KPI es inmutable.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.period_end < self.period_start:
            raise ValidationError("El fin del periodo no puede preceder al inicio.")
        if self.import_job.organization_id != self.indicator.organization_id:
            raise ValidationError("La carga y el indicador deben pertenecer a la organización.")
        if self.import_job.status != ImportJobStatus.PROCESSED:
            raise ValidationError("Solo una carga procesada puede originar observaciones.")
        if (
            self.import_job.template_version.template.target_type
            != TemplateTargetType.KPI_OBSERVATIONS
        ):
            raise ValidationError("La carga no corresponde a observaciones KPI.")
        site = self.site
        service = self.service
        source_row = self.source_row
        if self.site_id is not None and (
            site is None or site.organization_id != self.indicator.organization_id
        ):
            raise ValidationError("La sede no pertenece a la organización del indicador.")
        if self.service_id is not None:
            if service is None or self.site_id is None or service.site_id != self.site_id:
                raise ValidationError("El servicio debe pertenecer a la sede informada.")
        if self.source_row_id is not None and (
            source_row is None or source_row.import_job_id != self.import_job_id
        ):
            raise ValidationError("La fila fuente no pertenece a la carga informada.")

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las observaciones KPI no se eliminan físicamente.")


class IndicatorResult(AuditedIndicatorRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedIndicatorQuerySet.as_manager()

    indicator_version = models.ForeignKey(
        IndicatorVersion, on_delete=models.PROTECT, related_name="results"
    )
    site = models.ForeignKey(
        Site, null=True, blank=True, on_delete=models.PROTECT, related_name="indicator_results"
    )
    service = models.ForeignKey(
        Service,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicator_results",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    value = models.DecimalField(max_digits=20, decimal_places=6)
    performance_status = models.CharField(max_length=30, choices=PerformanceStatus.choices)
    status = models.CharField(max_length=30, choices=ResultStatus.choices)
    calculated_at = models.DateTimeField()
    calculated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="indicator_results_calculated",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicator_results_reviewed",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="indicator_results_published",
    )
    result_hash = models.CharField(max_length=64, unique=True)
    supersedes = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="corrections",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "indicators_result"
        ordering = ["indicator_version__indicator__code", "-period_start", "-calculated_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(period_end__gte=F("period_start")),
                name="indicator_result_dates_ck",
            ),
            models.CheckConstraint(
                condition=Q(status__in=ResultStatus.values), name="indicator_result_status_ck"
            ),
            models.CheckConstraint(
                condition=Q(performance_status__in=PerformanceStatus.values),
                name="indicator_performance_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(result_hash__regex=r"^[0-9a-f]{64}$"),
                name="indicator_result_hash_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status__in=[ResultStatus.PUBLISHED, ResultStatus.CORRECTED],
                        published_at__isnull=False,
                        published_by__isnull=False,
                    )
                    | (
                        ~Q(status__in=[ResultStatus.PUBLISHED, ResultStatus.CORRECTED])
                        & Q(published_at__isnull=True, published_by__isnull=True)
                    )
                ),
                name="indicator_result_publication_ck",
            ),
            models.CheckConstraint(
                condition=~Q(supersedes=F("id")), name="indicator_result_not_self_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=["indicator_version", "period_start", "status"],
                name="indicator_result_period_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.indicator_version.indicator.code} {self.period_start}: {self.value}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            immutable = (
                "indicator_version_id",
                "site_id",
                "service_id",
                "period_start",
                "period_end",
                "value",
                "performance_status",
                "calculated_at",
                "calculated_by_id",
                "result_hash",
                "supersedes_id",
            )
            if original.status in {ResultStatus.PUBLISHED, ResultStatus.CORRECTED} and any(
                getattr(original, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError("Un resultado publicado es inmutable.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.period_end < self.period_start:
            raise ValidationError("El fin del resultado no puede preceder al inicio.")
        organization_id = self.indicator_version.indicator.organization_id
        site = self.site
        service = self.service
        supersedes = self.supersedes
        if self.site_id is not None and (
            site is None or site.organization_id != organization_id
        ):
            raise ValidationError("La sede no pertenece al indicador.")
        if self.service_id is not None:
            if service is None or self.site_id is None or service.site_id != self.site_id:
                raise ValidationError("El servicio debe pertenecer a la sede del resultado.")
        if self.supersedes_id is not None:
            if self.supersedes_id == self.pk:
                raise ValidationError("Un resultado no puede corregirse a sí mismo.")
            if supersedes is None:
                raise ValidationError("El resultado sustituido no existe.")
            if (
                supersedes.indicator_version.indicator_id != self.indicator_version.indicator_id
            ):
                raise ValidationError("La corrección debe pertenecer al mismo indicador.")
            if (
                supersedes.period_start != self.period_start
                or supersedes.period_end != self.period_end
                or supersedes.site_id != self.site_id
                or supersedes.service_id != self.service_id
            ):
                raise ValidationError("La corrección debe conservar periodo y ámbito.")

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los resultados KPI no se eliminan físicamente.")


class ResultInput(models.Model):
    objects: ClassVar[models.Manager[Any]] = ProtectedIndicatorQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result = models.ForeignKey(
        IndicatorResult, on_delete=models.PROTECT, related_name="inputs"
    )
    observation = models.ForeignKey(
        IndicatorObservation, on_delete=models.PROTECT, related_name="result_inputs"
    )
    input_role = models.CharField(max_length=30)
    position = models.PositiveIntegerField()

    class Meta:
        db_table = "indicators_result_input"
        ordering = ["input_role", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["result", "observation"], name="indicator_result_observation_uq"
            ),
            models.UniqueConstraint(
                fields=["result", "input_role", "position"],
                name="indicator_result_role_position_uq",
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1), name="indicator_result_input_position_ck"
            ),
            models.CheckConstraint(
                condition=~Q(input_role=""), name="indicator_result_input_role_ck"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.input_role} {self.position}: {self.observation_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.input_role = self.input_role.strip().casefold()
        if self.result.status != ResultStatus.CALCULATED:
            raise ValidationError("Las entradas solo se fijan al crear el resultado.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if (
            self.observation.indicator_id
            != self.result.indicator_version.indicator_id
        ):
            raise ValidationError("La observación no pertenece al indicador del resultado.")

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las entradas de un resultado no se eliminan físicamente.")
