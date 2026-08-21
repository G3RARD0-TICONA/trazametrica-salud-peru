from __future__ import annotations

import uuid
from datetime import date
from typing import Any, ClassVar, NoReturn
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, Value
from django.db.models.functions import Lower
from django.utils import timezone


class ProtectedMasterQuerySet(models.QuerySet):
    def delete(self) -> NoReturn:
        raise ValidationError("Los maestros organizacionales no se eliminan; deben desactivarse.")


class ProtectedRecord(models.Model):
    objects: ClassVar[models.Manager[Any]] = ProtectedMasterQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los maestros organizacionales no se eliminan; deben desactivarse.")


class AuditedRecord(ProtectedRecord):
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


class CodedLifecycleMaster(AuditedRecord):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
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

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        super().save(*args, **kwargs)


LIFECYCLE_CONDITION = (
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
)


class Organization(CodedLifecycleMaster):
    timezone = models.CharField(max_length=64, default="America/Lima")
    demo_label = models.CharField(max_length=100, default="DATOS SINTÉTICOS")

    class Meta:
        db_table = "organizations_organization"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(Lower("code"), name="organizations_org_code_ci_uq"),
            models.UniqueConstraint(
                Value(1),
                condition=Q(is_active=True),
                name="organizations_one_active_org_uq",
            ),
            models.CheckConstraint(
                condition=LIFECYCLE_CONDITION,
                name="organizations_org_lifecycle_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name="") & ~Q(demo_label=""),
                name="organizations_org_required_text_ck",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as error:
            raise ValidationError({"timezone": "La zona horaria IANA no es válida."}) from error
        if "DATOS SINTÉTICOS" not in self.demo_label.upper():
            raise ValidationError(
                {"demo_label": "La organización demostrativa debe declarar DATOS SINTÉTICOS."}
            )


class Site(CodedLifecycleMaster):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="sites",
    )

    class Meta:
        db_table = "organizations_site"
        ordering = ["organization__code", "code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"),
                Lower("code"),
                name="organizations_site_scope_code_ci_uq",
            ),
            models.CheckConstraint(
                condition=LIFECYCLE_CONDITION,
                name="organizations_site_lifecycle_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name=""),
                name="organizations_site_required_text_ck",
            ),
        ]


class Service(CodedLifecycleMaster):
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="services")

    class Meta:
        db_table = "organizations_service"
        ordering = ["site__code", "code"]
        constraints = [
            models.UniqueConstraint(
                F("site"),
                Lower("code"),
                name="organizations_service_scope_code_ci_uq",
            ),
            models.CheckConstraint(
                condition=LIFECYCLE_CONDITION,
                name="organizations_service_lifecycle_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name=""),
                name="organizations_service_required_text_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["site", "is_active", "code"],
                name="organizations_service_catalog_ix",
            )
        ]


class Area(CodedLifecycleMaster):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="areas",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )

    class Meta:
        db_table = "organizations_area"
        ordering = ["organization__code", "code"]
        constraints = [
            models.UniqueConstraint(
                F("organization"),
                Lower("code"),
                name="organizations_area_scope_code_ci_uq",
            ),
            models.CheckConstraint(
                condition=LIFECYCLE_CONDITION,
                name="organizations_area_lifecycle_ck",
            ),
            models.CheckConstraint(
                condition=~Q(parent=F("id")),
                name="organizations_area_not_self_parent_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name=""),
                name="organizations_area_required_text_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "parent"],
                name="organizations_area_hierarchy_ix",
            )
        ]

    def clean(self) -> None:
        super().clean()
        parent = self.parent
        if parent is not None and parent.organization_id != self.organization_id:
            raise ValidationError({"parent": "El área padre debe pertenecer a la organización."})


class ResponsibilityType(models.TextChoices):
    AREA_OWNER = "AREA_OWNER", "Responsable del área"
    QUALITY_CONTACT = "QUALITY_CONTACT", "Contacto de calidad"
    DATA_STEWARD = "DATA_STEWARD", "Responsable de datos"
    BACKUP = "BACKUP", "Responsable suplente"


class ResponsibilityAssignment(AuditedRecord):
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="responsibility_assignments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organization_responsibilities",
    )
    responsibility_type = models.CharField(max_length=30, choices=ResponsibilityType.choices)
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "organizations_responsibility_assignment"
        ordering = ["area__code", "responsibility_type", "-valid_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["area", "user", "responsibility_type", "valid_from"],
                name="organizations_resp_start_uq",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="organizations_resp_dates_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["area", "responsibility_type", "valid_from", "valid_to"],
                name="organizations_resp_current_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.area.code}: {self.user.username} ({self.responsibility_type})"

    def is_current(self, on_date: date | None = None) -> bool:
        current_date = on_date or timezone.localdate()
        return self.valid_from <= current_date and (
            self.valid_to is None or self.valid_to >= current_date
        )
