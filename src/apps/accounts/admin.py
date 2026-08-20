from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Role, User, UserRole


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    readonly_fields = ("id", "created_at", "updated_at", "last_login", "date_joined")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Trazabilidad",
            {
                "fields": (
                    "id",
                    "created_at",
                    "created_by",
                    "updated_at",
                    "updated_by",
                    "bootstrap_reason",
                    "deactivated_at",
                    "deactivated_by",
                    "deactivation_reason",
                )
            },
        ),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_approval_role", "is_active")
    list_filter = ("is_active", "is_approval_role")
    search_fields = ("code", "name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "valid_from", "valid_to", "assigned_by")
    list_filter = ("role",)
    search_fields = ("user__username", "role__code")
    readonly_fields = ("id", "created_at", "updated_at")

