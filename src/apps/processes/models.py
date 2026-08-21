from __future__ import annotations

import re
import uuid
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.organizations.models import Area, Organization

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ProtectedProcessQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los procesos se modifican mediante servicios controlados.")

    def delete(self) -> NoReturn:
        raise ValidationError("Los procesos no se eliminan físicamente.")


class AuditedProcessRecord(models.Model):
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


class ProcessType(models.TextChoices):
    STRATEGIC = "strategic", "Estratégico"
    OPERATIONAL = "operational", "Operativo"
    SUPPORT = "support", "Soporte"


class ProcessVersionStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    IN_REVIEW = "in_review", "En revisión"
    APPROVED = "approved", "Aprobado"
    EFFECTIVE = "effective", "Vigente"
    SUPERSEDED = "superseded", "Sustituido"
    ANNULLED = "annulled", "Anulado"


class SipocEntryType(models.TextChoices):
    SUPPLIER = "supplier", "Proveedor"
    INPUT = "input", "Entrada"
    ACTIVITY = "activity", "Actividad"
    OUTPUT = "output", "Salida"
    CUSTOMER = "customer", "Cliente"


PROCESS_LIFECYCLE_CONDITION = Q(
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


class Process(AuditedProcessRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedProcessQuerySet.as_manager()

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="processes",
    )
    owner_area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="owned_processes",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    process_type = models.CharField(max_length=30, choices=ProcessType.choices)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="processes_process_deactivated",
    )
    deactivation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "processes_process"
        ordering = ["process_type", "code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"),
                Lower("code"),
                name="process_scope_code_ci_uq",
            ),
            models.CheckConstraint(
                condition=PROCESS_LIFECYCLE_CONDITION,
                name="process_lifecycle_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name=""),
                name="process_required_text_ck",
            ),
            models.CheckConstraint(
                condition=Q(process_type__in=ProcessType.values),
                name="process_type_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "process_type", "is_active", "code"],
                name="process_catalog_ix",
            ),
            models.Index(
                fields=["owner_area", "is_active"],
                name="process_owner_ix",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.owner_area.organization_id != self.organization_id:
            raise ValidationError(
                {"owner_area": "El área propietaria debe pertenecer a la organización."}
            )

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los procesos no se eliminan físicamente.")


class ProcessVersion(AuditedProcessRecord):
    objects: ClassVar[models.Manager[Any]] = ProtectedProcessQuerySet.as_manager()

    process = models.ForeignKey(
        Process,
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version_no = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=ProcessVersionStatus.choices)
    objective = models.TextField()
    scope = models.TextField()
    version_hash = models.CharField(max_length=64)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="process_versions_submitted",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="process_versions_reviewed",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="process_versions_approved",
    )
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "processes_process_version"
        ordering = ["process__code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["process", "version_no"],
                name="process_version_no_uq",
            ),
            models.CheckConstraint(
                condition=Q(version_no__gte=1),
                name="process_version_no_ck",
            ),
            models.CheckConstraint(
                condition=Q(status__in=ProcessVersionStatus.values),
                name="process_version_status_ck",
            ),
            models.CheckConstraint(
                condition=~Q(objective="") & ~Q(scope=""),
                name="process_version_text_ck",
            ),
            models.CheckConstraint(
                condition=Q(version_hash__regex=r"^[0-9a-f]{64}$"),
                name="process_version_hash_ck",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="process_version_dates_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["process", "status", "-version_no"],
                name="process_version_state_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.process.code} v{self.version_no} ({self.status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.objective = self.objective.strip()
        self.scope = self.scope.strip()
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            immutable = ("process_id", "version_no", "objective", "scope", "version_hash")
            if original.status != ProcessVersionStatus.DRAFT and any(
                getattr(original, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError("Una versión enviada o aprobada no permite cambiar su ficha.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not SHA256_PATTERN.fullmatch(self.version_hash):
            raise ValidationError({"version_hash": "El hash de versión no es SHA-256."})

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Las versiones de proceso no se eliminan físicamente.")


class SipocEntry(AuditedProcessRecord):
    process_version = models.ForeignKey(
        ProcessVersion,
        on_delete=models.PROTECT,
        related_name="sipoc_entries",
    )
    entry_type = models.CharField(max_length=20, choices=SipocEntryType.choices)
    position = models.PositiveIntegerField()
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "processes_sipoc_entry"
        ordering = ["entry_type", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["process_version", "entry_type", "position"],
                name="sipoc_type_position_uq",
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1),
                name="sipoc_position_ck",
            ),
            models.CheckConstraint(
                condition=Q(entry_type__in=SipocEntryType.values),
                name="sipoc_type_ck",
            ),
            models.CheckConstraint(condition=~Q(name=""), name="sipoc_name_ck"),
        ]
        indexes = [
            models.Index(
                fields=["process_version", "entry_type", "position"],
                name="sipoc_section_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_entry_type_display()} {self.position}: {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.name = self.name.strip()
        self.description = self.description.strip()
        if self.process_version.status != ProcessVersionStatus.DRAFT:
            raise ValidationError(
                "El SIPOC solo puede modificarse mientras la versión es borrador."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.process_version.status != ProcessVersionStatus.DRAFT:
            raise ValidationError("El SIPOC aprobado no se elimina.")
        return models.Model.delete(self, *args, **kwargs)
