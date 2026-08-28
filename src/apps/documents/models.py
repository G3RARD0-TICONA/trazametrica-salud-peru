from __future__ import annotations

import re
import uuid
from pathlib import PurePath
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.organizations.models import Area, Organization


class ProtectedDocumentQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError(
            "Los registros documentales se modifican mediante servicios controlados."
        )

    def delete(self) -> NoReturn:
        raise ValidationError("Los registros documentales no se eliminan físicamente.")


class ProtectedDocumentRecord(models.Model):
    objects: ClassVar[models.Manager[Any]] = ProtectedDocumentQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los registros documentales no se eliminan físicamente.")


class AuditedDocumentRecord(ProtectedDocumentRecord):
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


class LifecycleDocumentRecord(AuditedDocumentRecord):
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_deactivated",
    )
    deactivation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        abstract = True


LIFECYCLE_CONDITION = Q(
    is_active=True,
    deactivated_at__isnull=True,
    deactivated_by__isnull=True,
    deactivation_reason="",
) | (
    Q(
        is_active=False,
        deactivated_at__isnull=False,
        deactivated_by__isnull=False,
    )
    & ~Q(deactivation_reason="")
)


class ScanStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    CLEAN = "clean", "Limpio"
    REJECTED = "rejected", "Rechazado"
    ERROR = "error", "Error"


class VersionStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    APPROVED = "approved", "Aprobado"
    EFFECTIVE = "effective", "Vigente"
    SUPERSEDED = "superseded", "Sustituido"
    ANNULLED = "annulled", "Anulado"


class DocumentType(models.TextChoices):
    POLICY = "policy", "Política"
    PROCEDURE = "procedure", "Procedimiento"
    INSTRUCTION = "instruction", "Instructivo"
    FORM = "form", "Formato"
    RECORD = "record", "Registro"
    OTHER = "other", "Otro"


class ReferenceType(models.TextChoices):
    LAW = "law", "Ley"
    REGULATION = "regulation", "Reglamento"
    STANDARD = "standard", "Norma técnica"
    GUIDELINE = "guideline", "Guía"
    INTERNAL = "internal", "Referencia interna"


ALLOWED_FILE_MEDIA_TYPES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/csv",
        "text/plain",
    }
)
ALLOWED_FILE_SUFFIXES = frozenset({".pdf", ".xlsx", ".docx", ".csv", ".txt"})
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class FileAsset(AuditedDocumentRecord):
    storage_key = models.CharField(max_length=500, unique=True)
    original_name = models.CharField(max_length=255)
    media_type = models.CharField(max_length=150)
    size_bytes = models.BigIntegerField()
    sha256 = models.CharField(max_length=64)
    scan_status = models.CharField(
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
    )
    synthetic_confirmed = models.BooleanField(default=False)

    class Meta:
        db_table = "documents_file_asset"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(size_bytes__gt=0), name="doc_file_size_ck"),
            models.CheckConstraint(
                condition=Q(sha256__regex=r"^[0-9a-f]{64}$"),
                name="doc_file_hash_ck",
            ),
            models.CheckConstraint(
                condition=Q(scan_status__in=ScanStatus.values),
                name="doc_file_scan_ck",
            ),
            models.CheckConstraint(
                condition=Q(synthetic_confirmed=True),
                name="doc_file_synthetic_ck",
            ),
        ]
        indexes = [models.Index(fields=["sha256"], name="doc_file_hash_ix")]

    def __str__(self) -> str:
        return self.original_name

    def clean(self) -> None:
        super().clean()
        if PurePath(self.original_name).name != self.original_name:
            raise ValidationError({"original_name": "El nombre no debe contener una ruta."})
        if PurePath(self.original_name).suffix.lower() not in ALLOWED_FILE_SUFFIXES:
            raise ValidationError({"original_name": "La extensión documental no está permitida."})
        if self.media_type not in ALLOWED_FILE_MEDIA_TYPES:
            raise ValidationError({"media_type": "El tipo de archivo no está permitido."})
        if not SHA256_PATTERN.fullmatch(self.sha256):
            raise ValidationError(
                {"sha256": "El hash SHA-256 debe tener 64 caracteres hexadecimales."}
            )
        allowed_prefixes = ("documents/", "imports/", "reports/")
        if not self.storage_key.startswith(allowed_prefixes) or ".." in self.storage_key:
            raise ValidationError(
                {"storage_key": "La clave de almacenamiento no es opaca y segura."}
            )
        if not self.synthetic_confirmed:
            raise ValidationError({"synthetic_confirmed": "Solo se admiten archivos sintéticos."})


class Document(LifecycleDocumentRecord):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    responsible_area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="responsible_documents",
    )
    process = models.ForeignKey(
        "processes.Process",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=300)
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)

    class Meta:
        db_table = "documents_document"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"),
                Lower("code"),
                name="doc_scope_code_ci_uq",
            ),
            models.CheckConstraint(condition=LIFECYCLE_CONDITION, name="doc_lifecycle_ck"),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(title=""),
                name="doc_required_text_ck",
            ),
            models.CheckConstraint(
                condition=Q(document_type__in=DocumentType.values),
                name="doc_type_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "responsible_area", "is_active"],
                name="doc_catalog_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.title = self.title.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.responsible_area.organization_id != self.organization_id:
            raise ValidationError(
                {"responsible_area": "El área responsable debe pertenecer a la organización."}
            )
        linked_process = self.process if self.process_id is not None else None
        if linked_process is not None and linked_process.organization_id != self.organization_id:
            raise ValidationError(
                {"process": "El proceso debe pertenecer a la organización del documento."}
            )


class DocumentVersion(AuditedDocumentRecord):
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version_no = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=VersionStatus.choices)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="document_versions_submitted",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="document_versions_reviewed",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="document_versions_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)
    file_asset = models.ForeignKey(
        FileAsset,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="document_versions",
    )
    content = models.TextField(blank=True)
    version_hash = models.CharField(max_length=64)

    class Meta:
        db_table = "documents_document_version"
        ordering = ["document__code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_no"],
                name="doc_version_no_uq",
            ),
            models.CheckConstraint(condition=Q(version_no__gte=1), name="doc_version_no_ck"),
            models.CheckConstraint(
                condition=Q(status__in=VersionStatus.values),
                name="doc_version_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="doc_version_dates_ck",
            ),
            models.CheckConstraint(
                condition=(Q(file_asset__isnull=True) & ~Q(content=""))
                | (Q(file_asset__isnull=False) & Q(content="")),
                name="doc_version_payload_ck",
            ),
            models.CheckConstraint(
                condition=Q(version_hash__regex=r"^[0-9a-f]{64}$"),
                name="doc_version_hash_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["document", "status", "-version_no"],
                name="doc_version_state_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.document.code} v{self.version_no} ({self.status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.content = self.content.strip()
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            immutable = (
                "document_id",
                "version_no",
                "file_asset_id",
                "content",
                "version_hash",
            )
            if original.status != VersionStatus.DRAFT and any(
                getattr(original, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError(
                    "Una versión enviada o aprobada no permite cambiar contenido."
                )
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        has_content = bool(self.content.strip())
        has_file = self.file_asset_id is not None
        if has_content == has_file:
            raise ValidationError("La versión debe contener texto o un archivo, pero no ambos.")
        if has_file and self.file_asset is not None:
            if self.file_asset.scan_status != ScanStatus.CLEAN:
                raise ValidationError({"file_asset": "El archivo debe tener escaneo limpio."})
            if not self.file_asset.synthetic_confirmed:
                raise ValidationError(
                    {"file_asset": "El archivo debe estar confirmado como sintético."}
                )


class ReferenceSource(LifecycleDocumentRecord):
    code = models.CharField(max_length=50)
    issuer = models.CharField(max_length=200)
    title = models.CharField(max_length=500)
    source_url = models.URLField(max_length=1000, blank=True)
    reference_type = models.CharField(max_length=30, choices=ReferenceType.choices)

    class Meta:
        db_table = "documents_reference_source"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(Lower("code"), name="ref_code_ci_uq"),
            models.CheckConstraint(condition=LIFECYCLE_CONDITION, name="ref_lifecycle_ck"),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(issuer="") & ~Q(title=""),
                name="ref_required_text_ck",
            ),
            models.CheckConstraint(
                condition=Q(reference_type__in=ReferenceType.values),
                name="ref_type_ck",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.issuer = self.issuer.strip()
        self.title = self.title.strip()
        super().save(*args, **kwargs)


class ReferenceVersion(AuditedDocumentRecord):
    reference_source = models.ForeignKey(
        ReferenceSource,
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version_no = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=VersionStatus.choices)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reference_versions_submitted",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reference_versions_reviewed",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reference_versions_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    consulted_at = models.DateTimeField()
    summary = models.TextField()
    content_hash = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        db_table = "documents_reference_version"
        ordering = ["reference_source__code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["reference_source", "version_no"],
                name="ref_version_no_uq",
            ),
            models.CheckConstraint(condition=Q(version_no__gte=1), name="ref_version_no_ck"),
            models.CheckConstraint(
                condition=Q(status__in=VersionStatus.values),
                name="ref_version_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="ref_version_dates_ck",
            ),
            models.CheckConstraint(condition=~Q(summary=""), name="ref_summary_ck"),
            models.CheckConstraint(
                condition=Q(content_hash__isnull=True) | Q(content_hash__regex=r"^[0-9a-f]{64}$"),
                name="ref_content_hash_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["reference_source", "status", "-version_no"],
                name="ref_version_state_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.reference_source.code} v{self.version_no} ({self.status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.summary = self.summary.strip()
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            immutable = (
                "reference_source_id",
                "version_no",
                "publication_date",
                "consulted_at",
                "summary",
                "content_hash",
            )
            if original.status != VersionStatus.DRAFT and any(
                getattr(original, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError(
                    "Una referencia enviada o aprobada no permite cambiar contenido."
                )
        super().save(*args, **kwargs)
