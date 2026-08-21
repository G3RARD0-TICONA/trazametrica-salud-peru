from __future__ import annotations

import re
import uuid
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.documents.models import FileAsset
from apps.organizations.models import Organization

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ProtectedImportQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las importaciones se modifican mediante servicios controlados.")

    def delete(self) -> NoReturn:
        raise ValidationError("La evidencia de importación no se elimina físicamente.")


class AuditedImportRecord(models.Model):
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


class TemplateTargetType(models.TextChoices):
    KPI_OBSERVATIONS = "kpi_observations", "Observaciones KPI"
    AUDIT_FINDINGS = "audit_findings", "Hallazgos de auditoría"
    CORRECTIVE_ACTIONS = "corrective_actions", "Acciones correctivas"
    RISKS = "risks", "Riesgos"


class TemplateVersionStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    EFFECTIVE = "effective", "Vigente"
    SUPERSEDED = "superseded", "Sustituida"
    ANNULLED = "annulled", "Anulada"


class ImportJobStatus(models.TextChoices):
    RECEIVED = "received", "Recibida"
    VALIDATING = "validating", "Validando"
    REJECTED = "rejected", "Rechazada"
    ACCEPTED = "accepted", "Aceptada"
    PROCESSED = "processed", "Procesada"
    DUPLICATE = "duplicate", "Duplicada"
    FAILED = "failed", "Fallida"


class ImportErrorSeverity(models.TextChoices):
    BLOCKING = "blocking", "Bloqueante"
    WARNING = "warning", "Advertencia"


TEMPLATE_LIFECYCLE_CONDITION = Q(
    is_active=True,
    deactivated_at__isnull=True,
    deactivated_by__isnull=True,
    deactivation_reason="",
) | (
    Q(is_active=False, deactivated_at__isnull=False, deactivated_by__isnull=False)
    & ~Q(deactivation_reason="")
)


class ImportTemplate(AuditedImportRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedImportQuerySet.as_manager()

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="import_templates",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    target_type = models.CharField(max_length=30, choices=TemplateTargetType.choices)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="imports_template_deactivated",
    )
    deactivation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "imports_template"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"),
                Lower("code"),
                name="import_template_scope_code_ci_uq",
            ),
            models.CheckConstraint(
                condition=TEMPLATE_LIFECYCLE_CONDITION,
                name="import_template_lifecycle_ck",
            ),
            models.CheckConstraint(
                condition=Q(target_type__in=TemplateTargetType.values),
                name="import_template_target_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name=""),
                name="import_template_text_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "is_active", "code"],
                name="import_template_catalog_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las plantillas no se eliminan físicamente.")


class ImportTemplateVersion(AuditedImportRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedImportQuerySet.as_manager()

    template = models.ForeignKey(
        ImportTemplate,
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version_no = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=TemplateVersionStatus.choices)
    schema_definition = models.JSONField()
    file_asset = models.ForeignKey(
        FileAsset,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="import_template_versions",
    )
    schema_hash = models.CharField(max_length=64)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="import_template_versions_submitted",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="import_template_versions_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "imports_template_version"
        ordering = ["template__code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["template", "version_no"],
                name="import_template_version_no_uq",
            ),
            models.CheckConstraint(
                condition=Q(version_no__gte=1),
                name="import_template_version_no_ck",
            ),
            models.CheckConstraint(
                condition=Q(status__in=TemplateVersionStatus.values),
                name="import_template_version_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(schema_hash__regex=r"^[0-9a-f]{64}$"),
                name="import_template_schema_hash_ck",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="import_template_version_dates_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["template", "status", "-version_no"],
                name="imp_tpl_ver_state_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.template.code} v{self.version_no} ({self.status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            immutable = ("template_id", "version_no", "schema_definition", "schema_hash")
            if original.status != TemplateVersionStatus.DRAFT and any(
                getattr(original, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError("Una plantilla enviada o aprobada es inmutable.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not SHA256_PATTERN.fullmatch(self.schema_hash):
            raise ValidationError({"schema_hash": "El hash del esquema no es SHA-256."})

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las versiones de plantilla no se eliminan físicamente.")


class ImportJob(AuditedImportRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedImportQuerySet.as_manager()

    template_version = models.ForeignKey(
        ImportTemplateVersion,
        on_delete=models.PROTECT,
        related_name="import_jobs",
    )
    source_file = models.ForeignKey(
        FileAsset,
        on_delete=models.PROTECT,
        related_name="import_jobs",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="import_jobs",
    )
    status = models.CharField(max_length=30, choices=ImportJobStatus.choices)
    file_hash = models.CharField(max_length=64)
    row_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    promoted_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveIntegerField(default=1)
    duplicate_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="duplicate_attempts",
    )
    retry_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="retry_attempts",
    )

    class Meta:
        db_table = "imports_import_job"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=ImportJobStatus.values),
                name="import_job_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(file_hash__regex=r"^[0-9a-f]{64}$"),
                name="import_job_file_hash_ck",
            ),
            models.CheckConstraint(
                condition=Q(attempt_count__gte=1),
                name="import_job_attempt_ck",
            ),
            models.UniqueConstraint(
                fields=["organization", "file_hash"],
                condition=Q(status__in=[ImportJobStatus.ACCEPTED, ImportJobStatus.PROCESSED]),
                name="import_job_accepted_file_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "status", "-created_at"],
                name="import_job_queue_ix",
            ),
            models.Index(
                fields=["organization", "file_hash"],
                name="import_job_hash_ix",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.template_version} — {self.status}"

    def clean(self) -> None:
        super().clean()
        if self.template_version.template.organization_id != self.organization_id:
            raise ValidationError("La plantilla y la carga deben pertenecer a la organización.")
        if not SHA256_PATTERN.fullmatch(self.file_hash):
            raise ValidationError({"file_hash": "El hash del archivo no es SHA-256."})
        if self.duplicate_of_id is not None and self.duplicate_of_id == self.pk:
            raise ValidationError("Una carga no puede ser duplicada de sí misma.")
        if self.retry_of_id is not None and self.retry_of_id == self.pk:
            raise ValidationError("Una carga no puede ser reintento de sí misma.")

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las cargas no se eliminan físicamente.")


class ImportRow(models.Model):
    objects: ClassVar[models.Manager[Any]] = ProtectedImportQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_job = models.ForeignKey(
        ImportJob,
        on_delete=models.PROTECT,
        related_name="rows",
    )
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField()
    normalized_hash = models.CharField(max_length=64)
    is_valid = models.BooleanField(default=False)

    class Meta:
        db_table = "imports_import_row"
        ordering = ["row_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["import_job", "row_number"],
                name="import_row_number_uq",
            ),
            models.CheckConstraint(
                condition=Q(normalized_hash__regex=r"^[0-9a-f]{64}$"),
                name="import_row_hash_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["import_job", "is_valid", "row_number"],
                name="import_row_validation_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.import_job_id} fila {self.row_number}"

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las filas de staging no se eliminan físicamente.")


class ImportError(models.Model):
    objects: ClassVar[models.Manager[Any]] = ProtectedImportQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_row = models.ForeignKey(
        ImportRow,
        on_delete=models.PROTECT,
        related_name="errors",
    )
    column_name = models.CharField(max_length=100, blank=True)
    rule_code = models.CharField(max_length=50)
    severity = models.CharField(max_length=20, choices=ImportErrorSeverity.choices)
    message = models.CharField(max_length=500)
    suggested_action = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "imports_import_error"
        ordering = ["import_row__row_number", "column_name", "rule_code"]
        constraints = [
            models.CheckConstraint(
                condition=Q(severity__in=ImportErrorSeverity.values),
                name="import_error_severity_ck",
            ),
            models.CheckConstraint(
                condition=~Q(rule_code="") & ~Q(message=""),
                name="import_error_text_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["import_row", "severity"],
                name="import_error_row_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.rule_code}: {self.message}"

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los errores de importación no se eliminan físicamente.")
