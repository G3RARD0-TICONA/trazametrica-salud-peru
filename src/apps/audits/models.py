from __future__ import annotations

import re
import uuid
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.documents.models import FileAsset, ScanStatus
from apps.organizations.models import Organization

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ProtectedAuditQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los registros de auditoría se modifican mediante servicios.")

    def delete(self) -> NoReturn:
        raise ValidationError("La evidencia de auditoría no se elimina físicamente.")


class AuditedRecord(models.Model):
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
    objects: ClassVar[models.Manager[Any]] = ProtectedAuditQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("La evidencia de auditoría no se elimina físicamente.")


class AuditPlanStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    APPROVED = "approved", "Aprobado"
    IN_PROGRESS = "in_progress", "En ejecución"
    COMPLETED = "completed", "Completado"
    CANCELLED = "cancelled", "Cancelado"


class ChecklistVersionStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    EFFECTIVE = "effective", "Vigente"
    SUPERSEDED = "superseded", "Sustituida"
    ANNULLED = "annulled", "Anulada"


class ChecklistResponseType(models.TextChoices):
    COMPLIANCE = "compliance", "Conforme / no conforme"
    OBSERVATION = "observation", "Observación descriptiva"


class AuditExecutionStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "En ejecución"
    IN_REVIEW = "in_review", "En revisión"
    COMPLETED = "completed", "Completada"
    CANCELLED = "cancelled", "Cancelada"


class AuditResponseResult(models.TextChoices):
    CONFORM = "conform", "Conforme"
    NONCONFORM = "nonconform", "No conforme"
    NOT_APPLICABLE = "not_applicable", "No aplica"
    OBSERVATION = "observation", "Observación"


class FindingType(models.TextChoices):
    OBSERVATION = "observation", "Observación"
    OPPORTUNITY = "opportunity", "Oportunidad de mejora"
    NONCONFORMITY = "nonconformity", "No conformidad"


class FindingImpact(models.TextChoices):
    LOW = "low", "Bajo"
    MEDIUM = "medium", "Medio"
    HIGH = "high", "Alto"
    CRITICAL = "critical", "Crítico"


class FindingStatus(models.TextChoices):
    OPEN = "open", "Abierto"
    IN_ANALYSIS = "in_analysis", "En análisis"
    CANCELLED = "cancelled", "Cancelado"


class AuditPlan(AuditedRecord):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="audit_plans"
    )
    code = models.CharField(max_length=50)
    scope = models.TextField()
    criteria = models.TextField()
    lead_auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="led_audit_plans",
    )
    planned_start = models.DateField()
    planned_end = models.DateField()
    status = models.CharField(
        max_length=30, choices=AuditPlanStatus.choices, default=AuditPlanStatus.DRAFT
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_plans_submitted",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_plans_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "audits_audit_plan"
        ordering = ["-planned_start", "code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"), Lower("code"), name="audit_plan_scope_code_ci_uq"
            ),
            models.CheckConstraint(
                condition=Q(planned_end__gte=F("planned_start")),
                name="audit_plan_dates_ck",
            ),
            models.CheckConstraint(
                condition=Q(status__in=AuditPlanStatus.values), name="audit_plan_status_ck"
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(scope="") & ~Q(criteria=""),
                name="audit_plan_text_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "status", "planned_start"],
                name="audit_plan_catalog_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.scope}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.scope = self.scope.strip()
        self.criteria = self.criteria.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not self.lead_auditor.is_active:
            raise ValidationError("El auditor líder debe estar activo.")
        approval_complete = self.approved_at is not None and self.approved_by_id is not None
        if (self.approved_at is None) != (self.approved_by_id is None):
            raise ValidationError("La aprobación requiere fecha y aprobador.")
        if self.status in {
            AuditPlanStatus.APPROVED,
            AuditPlanStatus.IN_PROGRESS,
            AuditPlanStatus.COMPLETED,
        } and not approval_complete:
            raise ValidationError("El plan debe conservar su aprobación.")


class Checklist(AuditedRecord):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="audit_checklists"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_checklists_deactivated",
    )
    deactivation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "audits_checklist"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"), Lower("code"), name="audit_checklist_code_ci_uq"
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
                name="audit_checklist_lifecycle_ck",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        super().save(*args, **kwargs)


class ChecklistVersion(AuditedRecord):
    checklist = models.ForeignKey(
        Checklist, on_delete=models.PROTECT, related_name="versions"
    )
    version_no = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=ChecklistVersionStatus.choices)
    version_hash = models.CharField(max_length=64)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_checklist_versions_submitted",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_checklist_versions_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "audits_checklist_version"
        ordering = ["checklist__code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["checklist", "version_no"], name="audit_checklist_version_uq"
            ),
            models.CheckConstraint(
                condition=Q(version_no__gte=1), name="audit_checklist_version_no_ck"
            ),
            models.CheckConstraint(
                condition=Q(version_hash__regex=r"^[0-9a-f]{64}$"),
                name="audit_checklist_hash_ck",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="audit_checklist_dates_ck",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.checklist.code} v{self.version_no}"

    def clean(self) -> None:
        super().clean()
        if not SHA256_PATTERN.fullmatch(self.version_hash):
            raise ValidationError("El hash de la lista no es SHA-256 válido.")
        if (self.approved_at is None) != (self.approved_by_id is None):
            raise ValidationError("La aprobación requiere fecha y aprobador.")


class ChecklistItem(AuditedRecord):
    checklist_version = models.ForeignKey(
        ChecklistVersion, on_delete=models.PROTECT, related_name="items"
    )
    position = models.PositiveIntegerField()
    criterion = models.TextField()
    response_type = models.CharField(max_length=20, choices=ChecklistResponseType.choices)
    is_required = models.BooleanField(default=True)

    class Meta:
        db_table = "audits_checklist_item"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["checklist_version", "position"], name="audit_checklist_item_pos_uq"
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1), name="audit_checklist_item_pos_ck"
            ),
            models.CheckConstraint(
                condition=~Q(criterion=""), name="audit_checklist_item_text_ck"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.checklist_version} #{self.position}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.criterion = self.criterion.strip()
        super().save(*args, **kwargs)


class AuditExecution(AuditedRecord):
    audit_plan = models.ForeignKey(
        AuditPlan, on_delete=models.PROTECT, related_name="executions"
    )
    checklist_version = models.ForeignKey(
        ChecklistVersion, on_delete=models.PROTECT, related_name="executions"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=AuditExecutionStatus.choices)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_executions_submitted",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_executions_reviewed",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "audits_audit_execution"
        ordering = ["-started_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(completed_at__isnull=True) | Q(completed_at__gte=F("started_at")),
                name="audit_execution_dates_ck",
            ),
            models.CheckConstraint(
                condition=Q(status__in=AuditExecutionStatus.values),
                name="audit_execution_status_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["audit_plan", "status"], name="audit_execution_plan_ix")
        ]

    def __str__(self) -> str:
        return f"{self.audit_plan.code} — {self.get_status_display()}"

    def clean(self) -> None:
        super().clean()
        if (
            self.checklist_version.checklist.organization_id
            != self.audit_plan.organization_id
        ):
            raise ValidationError("El plan y la lista deben pertenecer a la misma organización.")
        if self.status == AuditExecutionStatus.COMPLETED and self.completed_at is None:
            raise ValidationError("Una ejecución completada requiere fecha de término.")

class AuditResponse(AuditedRecord):
    execution = models.ForeignKey(
        AuditExecution, on_delete=models.PROTECT, related_name="responses"
    )
    checklist_item = models.ForeignKey(
        ChecklistItem, on_delete=models.PROTECT, related_name="responses"
    )
    result = models.CharField(max_length=20, choices=AuditResponseResult.choices)
    observation = models.TextField(blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_responses",
    )
    responded_at = models.DateTimeField()

    class Meta:
        db_table = "audits_audit_response"
        ordering = ["checklist_item__position"]
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "checklist_item"], name="audit_response_item_uq"
            ),
            models.CheckConstraint(
                condition=Q(result__in=AuditResponseResult.values),
                name="audit_response_result_ck",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.execution.audit_plan.code} #{self.checklist_item.position}"

    def clean(self) -> None:
        super().clean()
        if self.checklist_item.checklist_version_id != self.execution.checklist_version_id:
            raise ValidationError("El criterio no pertenece a la lista ejecutada.")
        self.observation = self.observation.strip()
        if self.result in {
            AuditResponseResult.NONCONFORM,
            AuditResponseResult.NOT_APPLICABLE,
            AuditResponseResult.OBSERVATION,
        } and not self.observation:
            raise ValidationError("El resultado seleccionado requiere una observación.")
        if (
            self.checklist_item.response_type == ChecklistResponseType.OBSERVATION
            and self.result != AuditResponseResult.OBSERVATION
        ):
            raise ValidationError("El criterio descriptivo requiere resultado observación.")

class Finding(AuditedRecord):
    execution = models.ForeignKey(
        AuditExecution, on_delete=models.PROTECT, related_name="findings"
    )
    audit_response = models.ForeignKey(
        AuditResponse,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="findings",
    )
    code = models.CharField(max_length=50)
    finding_type = models.CharField(max_length=30, choices=FindingType.choices)
    criterion = models.TextField()
    condition = models.TextField()
    impact = models.CharField(max_length=20, choices=FindingImpact.choices)
    status = models.CharField(
        max_length=30, choices=FindingStatus.choices, default=FindingStatus.OPEN
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_audit_findings",
    )
    due_date = models.DateField(null=True, blank=True)
    evidence_absence_reason = models.CharField(max_length=500, blank=True)
    cancellation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "audits_finding"
        ordering = ["-created_at", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "code"], name="audit_finding_execution_code_uq"
            ),
            models.CheckConstraint(
                condition=Q(finding_type__in=FindingType.values), name="audit_finding_type_ck"
            ),
            models.CheckConstraint(
                condition=Q(impact__in=FindingImpact.values), name="audit_finding_impact_ck"
            ),
            models.CheckConstraint(
                condition=Q(status__in=FindingStatus.values), name="audit_finding_status_ck"
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(criterion="") & ~Q(condition=""),
                name="audit_finding_text_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "impact", "due_date"], name="audit_finding_alert_ix")
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.get_finding_type_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.criterion = self.criterion.strip()
        self.condition = self.condition.strip()
        self.evidence_absence_reason = self.evidence_absence_reason.strip()
        self.cancellation_reason = self.cancellation_reason.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not self.owner.is_active:
            raise ValidationError("El responsable del hallazgo debe estar activo.")
        if self.audit_response_id is not None:
            response = self.audit_response
            if response is not None and response.execution_id != self.execution_id:
                raise ValidationError("La respuesta y el hallazgo deben pertenecer a la ejecución.")
        if self.status == FindingStatus.CANCELLED and not self.cancellation_reason:
            raise ValidationError("La cancelación requiere un motivo.")


class FindingEvidence(AuditedRecord):
    finding = models.ForeignKey(
        Finding, on_delete=models.PROTECT, related_name="evidence"
    )
    file_asset = models.ForeignKey(
        FileAsset, on_delete=models.PROTECT, related_name="finding_evidence_links"
    )
    description = models.CharField(max_length=500)

    class Meta:
        db_table = "audits_finding_evidence"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["finding", "file_asset"], name="audit_finding_evidence_uq"
            ),
            models.CheckConstraint(
                condition=~Q(description=""), name="audit_finding_evidence_text_ck"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.finding.code} — {self.file_asset.original_name}"

    def clean(self) -> None:
        super().clean()
        self.description = self.description.strip()
        if self.file_asset.scan_status != ScanStatus.CLEAN:
            raise ValidationError("La evidencia debe superar la validación de archivo.")
        if not self.file_asset.synthetic_confirmed:
            raise ValidationError("Solo se admite evidencia sintética.")
