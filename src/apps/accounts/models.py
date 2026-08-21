import uuid
from datetime import date
from typing import Any, ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.utils import timezone

from .managers import UserManager


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users_created",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users_updated",
    )
    bootstrap_reason = models.CharField(max_length=500, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users_deactivated",
    )
    deactivation_reason = models.CharField(max_length=500, blank=True)

    objects: ClassVar[UserManager] = UserManager()

    class Meta:
        db_table = "accounts_user"
        constraints = [
            models.UniqueConstraint(Lower("username"), name="accounts_user_username_ci_uq"),
            models.CheckConstraint(
                condition=(
                    Q(created_by__isnull=False)
                    | (Q(is_superuser=True) & ~Q(bootstrap_reason=""))
                ),
                name="accounts_user_bootstrap_actor_ck",
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
                name="accounts_user_deactivation_ck",
            ),
        ]


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_approval_role = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="roles_created",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="roles_updated",
    )
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="roles_deactivated",
    )
    deactivation_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "accounts_role"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(Lower("code"), name="accounts_role_code_ci_uq"),
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
                name="accounts_role_deactivation_ck",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="role_assignments",
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="assignments")
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="role_assignments_authorized",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="user_roles_created",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="user_roles_updated",
    )

    class Meta:
        db_table = "accounts_user_role"
        ordering = ["user__username", "role__code", "-valid_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role", "valid_from"],
                name="accounts_user_role_start_uq",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="accounts_user_role_dates_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "valid_from", "valid_to"],
                name="accounts_usr_role_valid_ix",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.username}: {self.role.code}"

    def is_current(self, on_date: date | None = None) -> bool:
        current_date = on_date or timezone.localdate()
        return self.valid_from <= current_date and (
            self.valid_to is None or self.valid_to >= current_date
        )
