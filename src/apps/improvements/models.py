from __future__ import annotations

import uuid
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.audits.models import Finding
from apps.documents.models import FileAsset, ScanStatus


class ProtectedImprovementQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los registros de mejora se modifican mediante servicios.")

    def delete(self) -> NoReturn:
        raise ValidationError("La evidencia de mejora no se elimina físicamente.")


class AuditedImprovementRecord(models.Model):
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
    objects: ClassVar[models.Manager[Any]] = ProtectedImprovementQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("La evidencia de mejora no se elimina físicamente.")


class RootCauseMethod(models.TextChoices):
    FIVE_WHYS = "five_whys", "Cinco porqués"
    ISHIKAWA = "ishikawa", "Ishikawa"
    PARETO = "pareto", "Pareto"
    OTHER = "other", "Otro método documentado"


class RootCauseStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    APPROVED = "approved", "Aprobado"


class CorrectiveActionStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    IN_REVIEW = "in_review", "En revisión"
    IN_PROGRESS = "in_progress", "En ejecución"
    IN_VERIFICATION = "in_verification", "En verificación"
    CLOSED = "closed", "Cerrada"
    REOPENED = "reopened", "Reabierta"
    CANCELLED = "cancelled", "Cancelada"


class EffectivenessResult(models.TextChoices):
    EFFECTIVE = "effective", "Eficaz"
    INEFFECTIVE = "ineffective", "No eficaz"


class RootCauseAnalysis(AuditedImprovementRecord):
    finding = models.OneToOneField(
        Finding, on_delete=models.PROTECT, related_name="root_cause_analysis"
    )
    method = models.CharField(max_length=30, choices=RootCauseMethod.choices)
    analysis = models.TextField()
    conclusion = models.TextField()
    status = models.CharField(
        max_length=30, choices=RootCauseStatus.choices, default=RootCauseStatus.DRAFT
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="root_cause_analyses_submitted",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="root_cause_analyses_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "improvements_root_cause_analysis"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(method__in=RootCauseMethod.values),
                name="improvement_root_method_ck",
            ),
            models.CheckConstraint(
                condition=Q(status__in=RootCauseStatus.values),
                name="improvement_root_status_ck",
            ),
            models.CheckConstraint(
                condition=~Q(analysis="") & ~Q(conclusion=""),
                name="improvement_root_text_ck",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.finding.code} — {self.get_method_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.analysis = self.analysis.strip()
        self.conclusion = self.conclusion.strip()
        self.decision_reason = self.decision_reason.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not self.analysis.strip() or not self.conclusion.strip():
            raise ValidationError("El análisis y la conclusión causal son obligatorios.")
        if (self.approved_at is None) != (self.approved_by_id is None):
            raise ValidationError("La aprobación causal requiere fecha y aprobador.")
        if self.status == RootCauseStatus.APPROVED and self.approved_at is None:
            raise ValidationError("Una causa aprobada debe conservar su aprobación.")


class CorrectiveAction(AuditedImprovementRecord):
    finding = models.ForeignKey(
        Finding, on_delete=models.PROTECT, related_name="corrective_actions"
    )
    root_cause = models.ForeignKey(
        RootCauseAnalysis, on_delete=models.PROTECT, related_name="corrective_actions"
    )
    code = models.CharField(max_length=50)
    description = models.TextField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_corrective_actions",
    )
    due_date = models.DateField()
    status = models.CharField(
        max_length=30,
        choices=CorrectiveActionStatus.choices,
        default=CorrectiveActionStatus.PENDING,
    )
    effectiveness_criterion = models.TextField()
    is_mandatory = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="corrective_actions_submitted",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="corrective_actions_approved",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="corrective_actions_completed",
    )
    decision_reason = models.CharField(max_length=500, blank=True)
    cancellation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "improvements_corrective_action"
        ordering = ["due_date", "code"]
        constraints = [
            models.UniqueConstraint(
                F("finding"), Lower("code"), name="improvement_action_code_ci_uq"
            ),
            models.CheckConstraint(
                condition=Q(status__in=CorrectiveActionStatus.values),
                name="improvement_action_status_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(description="") & ~Q(effectiveness_criterion=""),
                name="improvement_action_text_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["status", "due_date", "owner"], name="improvement_action_alert_ix"
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.description}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.description = self.description.strip()
        self.effectiveness_criterion = self.effectiveness_criterion.strip()
        self.decision_reason = self.decision_reason.strip()
        self.cancellation_reason = self.cancellation_reason.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.root_cause.finding_id != self.finding_id:
            raise ValidationError("La causa y la acción deben pertenecer al mismo hallazgo.")
        if not self.description.strip() or not self.effectiveness_criterion.strip():
            raise ValidationError("La acción y su criterio de eficacia son obligatorios.")
        if (self.approved_at is None) != (self.approved_by_id is None):
            raise ValidationError("La aprobación de la acción requiere fecha y aprobador.")
        if (self.completed_at is None) != (self.completed_by_id is None):
            raise ValidationError("La terminación requiere fecha y ejecutor.")
        if self.status == CorrectiveActionStatus.CANCELLED and not self.cancellation_reason:
            raise ValidationError("La cancelación requiere un motivo.")


class ActionEvidence(AuditedImprovementRecord):
    action = models.ForeignKey(
        CorrectiveAction, on_delete=models.PROTECT, related_name="evidence"
    )
    file_asset = models.ForeignKey(
        FileAsset, on_delete=models.PROTECT, related_name="action_evidence_links"
    )
    description = models.CharField(max_length=500)

    class Meta:
        db_table = "improvements_action_evidence"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["action", "file_asset"], name="improvement_action_evidence_uq"
            ),
            models.CheckConstraint(
                condition=~Q(description=""), name="improvement_evidence_text_ck"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.action.code} — {self.file_asset.original_name}"

    def clean(self) -> None:
        super().clean()
        self.description = self.description.strip()
        if not self.description:
            raise ValidationError("La evidencia requiere descripción.")
        if self.file_asset.scan_status != ScanStatus.CLEAN:
            raise ValidationError("La evidencia debe superar la validación de archivo.")
        if not self.file_asset.synthetic_confirmed:
            raise ValidationError("Solo se admite evidencia sintética.")


class EffectivenessReview(AuditedImprovementRecord):
    action = models.ForeignKey(
        CorrectiveAction, on_delete=models.PROTECT, related_name="effectiveness_reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="effectiveness_reviews",
    )
    reviewed_at = models.DateTimeField()
    result = models.CharField(max_length=20, choices=EffectivenessResult.choices)
    notes = models.TextField()
    reopens_action = models.BooleanField()

    class Meta:
        db_table = "improvements_effectiveness_review"
        ordering = ["-reviewed_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(result__in=EffectivenessResult.values),
                name="improvement_review_result_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(result=EffectivenessResult.EFFECTIVE, reopens_action=False)
                    | Q(result=EffectivenessResult.INEFFECTIVE, reopens_action=True)
                ),
                name="improvement_review_reopen_ck",
            ),
            models.CheckConstraint(
                condition=~Q(notes=""), name="improvement_review_notes_ck"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.action.code} — {self.get_result_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.notes = self.notes.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not self.notes.strip():
            raise ValidationError("La revisión de eficacia requiere notas.")
        if self.reopens_action != (self.result == EffectivenessResult.INEFFECTIVE):
            raise ValidationError("La reapertura debe corresponder al resultado no eficaz.")
