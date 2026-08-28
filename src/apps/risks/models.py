from __future__ import annotations

import uuid
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.audits.models import Finding
from apps.improvements.models import CorrectiveAction
from apps.indicators.models import Indicator
from apps.organizations.models import Organization
from apps.processes.models import Process


class ProtectedRiskQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los registros de riesgo se modifican mediante servicios.")

    def delete(self) -> NoReturn:
        raise ValidationError("La evidencia de riesgo no se elimina físicamente.")


class AuditedRiskRecord(models.Model):
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
    objects: ClassVar[models.Manager[Any]] = ProtectedRiskQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("La evidencia de riesgo no se elimina físicamente.")


class RiskStatus(models.TextChoices):
    IDENTIFIED = "identified", "Identificado"
    ASSESSED = "assessed", "Evaluado"
    UNDER_TREATMENT = "under_treatment", "En tratamiento"
    CONTROLLED = "controlled", "Controlado"
    ACCEPTED = "accepted", "Aceptado"
    CLOSED = "closed", "Cerrado"
    REOPENED = "reopened", "Reabierto"


class AssessmentStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    APPROVED = "approved", "Aprobada"
    SUPERSEDED = "superseded", "Sustituida"


class RiskLevel(models.TextChoices):
    LOW = "low", "Bajo"
    MEDIUM = "medium", "Medio"
    HIGH = "high", "Alto"
    CRITICAL = "critical", "Crítico"


class ControlVersionStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    EFFECTIVE = "effective", "Vigente"
    SUPERSEDED = "superseded", "Sustituida"
    ANNULLED = "annulled", "Anulada"


class ControlType(models.TextChoices):
    PREVENTIVE = "preventive", "Preventivo"
    DETECTIVE = "detective", "Detectivo"
    CORRECTIVE = "corrective", "Correctivo"


class ControlFrequency(models.TextChoices):
    CONTINUOUS = "continuous", "Continuo"
    DAILY = "daily", "Diario"
    WEEKLY = "weekly", "Semanal"
    MONTHLY = "monthly", "Mensual"
    QUARTERLY = "quarterly", "Trimestral"
    SEMIANNUAL = "semiannual", "Semestral"
    ANNUAL = "annual", "Anual"


class ExpectedEffectiveness(models.TextChoices):
    LOW = "low", "Baja"
    MEDIUM = "medium", "Media"
    HIGH = "high", "Alta"


class ControlReviewResult(models.TextChoices):
    EFFECTIVE = "effective", "Eficaz"
    PARTIALLY_EFFECTIVE = "partially_effective", "Parcialmente eficaz"
    INEFFECTIVE = "ineffective", "Ineficaz"


def risk_level_for(score: int) -> RiskLevel:
    if score < 1 or score > 25:
        raise ValidationError("El nivel de riesgo debe estar entre 1 y 25.")
    if score <= 4:
        return RiskLevel.LOW
    if score <= 9:
        return RiskLevel.MEDIUM
    if score <= 16:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


class Risk(AuditedRiskRecord):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="risks"
    )
    process = models.ForeignKey(Process, on_delete=models.PROTECT, related_name="risks")
    code = models.CharField(max_length=50)
    cause = models.TextField()
    event = models.TextField()
    consequence = models.TextField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_risks",
    )
    status = models.CharField(
        max_length=30, choices=RiskStatus.choices, default=RiskStatus.IDENTIFIED
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "risks_risk"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"), Lower("code"), name="risk_scope_code_ci_uq"
            ),
            models.CheckConstraint(
                condition=Q(status__in=RiskStatus.values), name="risk_status_ck"
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(cause="") & ~Q(event="") & ~Q(consequence=""),
                name="risk_required_text_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "process", "status"], name="risk_catalog_ix"
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.event}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.cause = self.cause.strip()
        self.event = self.event.strip()
        self.consequence = self.consequence.strip()
        self.decision_reason = self.decision_reason.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.process.organization_id != self.organization_id:
            raise ValidationError("El proceso y el riesgo deben pertenecer a la organización.")
        if not self.owner.is_active:
            raise ValidationError("El responsable del riesgo debe estar activo.")
        if not self.cause.strip() or not self.event.strip() or not self.consequence.strip():
            raise ValidationError("Causa, evento y consecuencia son obligatorios.")


class RiskAssessment(AuditedRiskRecord):
    risk = models.ForeignKey(Risk, on_delete=models.PROTECT, related_name="assessments")
    version_no = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, choices=AssessmentStatus.choices, default=AssessmentStatus.DRAFT
    )
    probability = models.PositiveSmallIntegerField()
    impact = models.PositiveSmallIntegerField()
    inherent_level = models.PositiveSmallIntegerField()
    inherent_band = models.CharField(max_length=20, choices=RiskLevel.choices)
    residual_probability = models.PositiveSmallIntegerField(null=True, blank=True)
    residual_impact = models.PositiveSmallIntegerField(null=True, blank=True)
    residual_level = models.PositiveSmallIntegerField(null=True, blank=True)
    residual_band = models.CharField(
        max_length=20, choices=RiskLevel.choices, blank=True
    )
    assessed_at = models.DateTimeField()
    next_review_date = models.DateField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="risk_assessments_submitted",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="risk_assessments_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "risks_risk_assessment"
        ordering = ["risk__code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["risk", "version_no"], name="risk_assessment_version_uq"
            ),
            models.CheckConstraint(
                condition=Q(version_no__gte=1), name="risk_assessment_version_ck"
            ),
            models.CheckConstraint(
                condition=Q(probability__gte=1, probability__lte=5),
                name="risk_probability_ck",
            ),
            models.CheckConstraint(
                condition=Q(impact__gte=1, impact__lte=5), name="risk_impact_ck"
            ),
            models.CheckConstraint(
                condition=Q(inherent_level=F("probability") * F("impact")),
                name="risk_inherent_product_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        residual_probability__isnull=True,
                        residual_impact__isnull=True,
                        residual_level__isnull=True,
                        residual_band="",
                    )
                    | Q(
                        residual_probability__gte=1,
                        residual_probability__lte=5,
                        residual_impact__gte=1,
                        residual_impact__lte=5,
                        residual_level=F("residual_probability") * F("residual_impact"),
                    )
                ),
                name="risk_residual_complete_ck",
            ),
            models.CheckConstraint(
                condition=Q(status__in=AssessmentStatus.values),
                name="risk_assessment_status_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["risk", "status", "-version_no"], name="risk_assessment_state_ix"
            ),
            models.Index(fields=["status", "next_review_date"], name="risk_review_alert_ix"),
        ]

    def __str__(self) -> str:
        return f"{self.risk.code} v{self.version_no}"

    def clean(self) -> None:
        super().clean()
        expected_inherent = self.probability * self.impact
        if self.inherent_level != expected_inherent:
            raise ValidationError("El riesgo inherente debe ser probabilidad × impacto.")
        if self.inherent_band != risk_level_for(expected_inherent):
            raise ValidationError("La clasificación inherente no corresponde a su nivel.")
        residual_values = (
            self.residual_probability,
            self.residual_impact,
            self.residual_level,
        )
        if any(value is not None for value in residual_values):
            if any(value is None for value in residual_values):
                raise ValidationError("La evaluación residual debe estar completa.")
            residual_probability = int(self.residual_probability or 0)
            residual_impact = int(self.residual_impact or 0)
            expected_residual = residual_probability * residual_impact
            if self.residual_level != expected_residual:
                raise ValidationError("El riesgo residual debe ser probabilidad × impacto.")
            if self.residual_band != risk_level_for(expected_residual):
                raise ValidationError("La clasificación residual no corresponde a su nivel.")
        elif self.residual_band:
            raise ValidationError("No puede existir clasificación residual sin evaluación.")
        if (self.approved_at is None) != (self.approved_by_id is None):
            raise ValidationError("La aprobación requiere fecha y aprobador.")
        if self.status == AssessmentStatus.APPROVED and self.approved_at is None:
            raise ValidationError("Una evaluación aprobada debe conservar la aprobación.")


class Control(AuditedRiskRecord):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="controls"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_controls",
    )
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="controls_deactivated",
    )
    deactivation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "risks_control"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"), Lower("code"), name="control_scope_code_ci_uq"
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        is_active=True,
                        deactivated_at__isnull=True,
                        deactivated_by__isnull=True,
                        deactivation_reason="",
                    )
                    | (
                        Q(
                            is_active=False,
                            deactivated_at__isnull=False,
                            deactivated_by__isnull=False,
                        )
                        & ~Q(deactivation_reason="")
                    )
                ),
                name="control_lifecycle_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name=""), name="control_required_text_ck"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        self.deactivation_reason = self.deactivation_reason.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not self.owner.is_active:
            raise ValidationError("El responsable del control debe estar activo.")


class ControlVersion(AuditedRiskRecord):
    control = models.ForeignKey(Control, on_delete=models.PROTECT, related_name="versions")
    version_no = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=ControlVersionStatus.choices,
        default=ControlVersionStatus.DRAFT,
    )
    description = models.TextField()
    control_type = models.CharField(max_length=20, choices=ControlType.choices)
    frequency = models.CharField(max_length=20, choices=ControlFrequency.choices)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="control_versions_submitted",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="control_versions_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "risks_control_version"
        ordering = ["control__code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["control", "version_no"], name="control_version_no_uq"
            ),
            models.CheckConstraint(
                condition=Q(version_no__gte=1), name="control_version_no_ck"
            ),
            models.CheckConstraint(
                condition=Q(status__in=ControlVersionStatus.values),
                name="control_version_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="control_version_dates_ck",
            ),
            models.CheckConstraint(
                condition=~Q(description=""), name="control_version_text_ck"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.control.code} v{self.version_no}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.description = self.description.strip()
        self.decision_reason = self.decision_reason.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not self.description.strip():
            raise ValidationError("La versión del control requiere descripción.")
        if (self.approved_at is None) != (self.approved_by_id is None):
            raise ValidationError("La aprobación requiere fecha y aprobador.")
        if self.status == ControlVersionStatus.EFFECTIVE:
            if self.approved_at is None or self.valid_from is None:
                raise ValidationError("Un control vigente requiere aprobación y fecha inicial.")


class RiskControl(AuditedRiskRecord):
    risk = models.ForeignKey(Risk, on_delete=models.PROTECT, related_name="risk_controls")
    control_version = models.ForeignKey(
        ControlVersion, on_delete=models.PROTECT, related_name="risk_controls"
    )
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    effectiveness_expected = models.CharField(
        max_length=20, choices=ExpectedEffectiveness.choices
    )

    class Meta:
        db_table = "risks_risk_control"
        ordering = ["risk__code", "control_version__control__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["risk", "control_version", "valid_from"],
                name="risk_control_period_uq",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="risk_control_dates_ck",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.risk.code} — {self.control_version.control.code}"

    def clean(self) -> None:
        super().clean()
        if self.risk.organization_id != self.control_version.control.organization_id:
            raise ValidationError("El riesgo y el control deben pertenecer a la organización.")
        if self.control_version.status != ControlVersionStatus.EFFECTIVE:
            raise ValidationError("Solo una versión vigente puede vincularse al riesgo.")
        if (
            self.control_version.valid_from is None
            or self.valid_from < self.control_version.valid_from
        ):
            raise ValidationError("El vínculo no puede iniciar antes de la versión vigente.")


class ControlReview(AuditedRiskRecord):
    risk_control = models.ForeignKey(
        RiskControl, on_delete=models.PROTECT, related_name="reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="control_reviews",
    )
    reviewed_at = models.DateTimeField()
    result = models.CharField(max_length=30, choices=ControlReviewResult.choices)
    notes = models.TextField()
    next_review_date = models.DateField()

    class Meta:
        db_table = "risks_control_review"
        ordering = ["-reviewed_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(result__in=ControlReviewResult.values),
                name="control_review_result_ck",
            ),
            models.CheckConstraint(
                condition=~Q(notes=""), name="control_review_notes_ck"
            ),
        ]
        indexes = [
            models.Index(fields=["next_review_date"], name="control_review_alert_ix")
        ]

    def __str__(self) -> str:
        return f"{self.risk_control} — {self.get_result_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.notes = self.notes.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not self.notes.strip():
            raise ValidationError("La revisión del control requiere notas.")
        if self.next_review_date <= self.reviewed_at.date():
            raise ValidationError("La próxima revisión debe ser posterior a la revisión actual.")


class RiskIndicatorLink(AuditedRiskRecord):
    risk = models.ForeignKey(Risk, on_delete=models.PROTECT, related_name="indicator_links")
    indicator = models.ForeignKey(
        Indicator, on_delete=models.PROTECT, related_name="risk_links"
    )

    class Meta:
        db_table = "risks_risk_indicator"
        constraints = [
            models.UniqueConstraint(
                fields=["risk", "indicator"], name="risk_indicator_link_uq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.risk.code} — {self.indicator.code}"

    def clean(self) -> None:
        super().clean()
        if self.risk.organization_id != self.indicator.organization_id:
            raise ValidationError("El riesgo y el indicador deben pertenecer a la organización.")


class RiskFindingLink(AuditedRiskRecord):
    risk = models.ForeignKey(Risk, on_delete=models.PROTECT, related_name="finding_links")
    finding = models.ForeignKey(Finding, on_delete=models.PROTECT, related_name="risk_links")

    class Meta:
        db_table = "risks_risk_finding"
        constraints = [
            models.UniqueConstraint(
                fields=["risk", "finding"], name="risk_finding_link_uq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.risk.code} — {self.finding.code}"

    def clean(self) -> None:
        super().clean()
        organization_id = self.finding.execution.audit_plan.organization_id
        if self.risk.organization_id != organization_id:
            raise ValidationError("El riesgo y el hallazgo deben pertenecer a la organización.")


class RiskActionLink(AuditedRiskRecord):
    risk = models.ForeignKey(Risk, on_delete=models.PROTECT, related_name="action_links")
    action = models.ForeignKey(
        CorrectiveAction, on_delete=models.PROTECT, related_name="risk_links"
    )

    class Meta:
        db_table = "risks_risk_action"
        constraints = [
            models.UniqueConstraint(
                fields=["risk", "action"], name="risk_action_link_uq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.risk.code} — {self.action.code}"

    def clean(self) -> None:
        super().clean()
        organization_id = self.action.finding.execution.audit_plan.organization_id
        if self.risk.organization_id != organization_id:
            raise ValidationError("El riesgo y la acción deben pertenecer a la organización.")
