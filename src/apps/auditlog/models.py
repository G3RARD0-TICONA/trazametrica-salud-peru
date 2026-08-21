from __future__ import annotations

import uuid
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("La bitácora es inmutable y no admite actualizaciones.")

    def delete(self) -> NoReturn:
        raise ValidationError("La bitácora es inmutable y no admite eliminaciones.")


class EventResult(models.TextChoices):
    SUCCESS = "success", "Correcto"
    DENIED = "denied", "Denegado"
    ERROR = "error", "Error"
    CANCELLED = "cancelled", "Cancelado"


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurred_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_events",
    )
    correlation_id = models.UUIDField()
    object_type = models.CharField(max_length=100)
    object_id = models.UUIDField(null=True, blank=True)
    action = models.CharField(max_length=50)
    result = models.CharField(max_length=20, choices=EventResult.choices)
    reason = models.CharField(max_length=500, blank=True)
    context = models.JSONField(default=dict, blank=True)
    event_hash = models.CharField(max_length=64, unique=True)

    objects: ClassVar[models.Manager[Any]] = AppendOnlyQuerySet.as_manager()

    class Meta:
        db_table = "auditlog_event"
        ordering = ["-occurred_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(result__in=EventResult.values),
                name="audit_result_ck",
            ),
            models.CheckConstraint(
                condition=Q(event_hash__regex=r"^[0-9a-f]{64}$"),
                name="audit_hash_ck",
            ),
            models.CheckConstraint(
                condition=~Q(object_type="") & ~Q(action=""),
                name="audit_required_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["object_type", "object_id", "-occurred_at"],
                name="audit_obj_time_ix",
            ),
            models.Index(
                fields=["correlation_id", "occurred_at"],
                name="audit_corr_time_ix",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.occurred_at.isoformat()} {self.object_type}:{self.action}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValidationError("La bitácora es inmutable y no admite actualizaciones.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("La bitácora es inmutable y no admite eliminaciones.")
