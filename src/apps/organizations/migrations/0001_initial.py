# Generated for Django 5.2.17 on 2026-08-20.

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=50)),
                ("name", models.CharField(max_length=200)),
                ("is_active", models.BooleanField(default=True)),
                ("deactivated_at", models.DateTimeField(blank=True, null=True)),
                ("deactivation_reason", models.CharField(blank=True, max_length=500)),
                ("timezone", models.CharField(default="America/Lima", max_length=64)),
                (
                    "demo_label",
                    models.CharField(default="DATOS SINTÉTICOS", max_length=100),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_organization_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "deactivated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_organization_deactivated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_organization_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "organizations_organization",
                "ordering": ["code"],
                "constraints": [
                    models.UniqueConstraint(
                        Lower("code"),
                        name="organizations_org_code_ci_uq",
                    ),
                    models.UniqueConstraint(
                        models.Value(1),
                        condition=models.Q(("is_active", True)),
                        name="organizations_one_active_org_uq",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(
                                ("deactivated_at__isnull", True),
                                ("deactivated_by__isnull", True),
                                ("deactivation_reason", ""),
                                ("is_active", True),
                            )
                            | (
                                models.Q(
                                    ("deactivated_at__isnull", False),
                                    ("deactivated_by__isnull", False),
                                    ("is_active", False),
                                )
                                & ~models.Q(("deactivation_reason", ""))
                            )
                        ),
                        name="organizations_org_lifecycle_ck",
                    ),
                    models.CheckConstraint(
                        condition=(
                            ~models.Q(("code", ""))
                            & ~models.Q(("name", ""))
                            & ~models.Q(("demo_label", ""))
                        ),
                        name="organizations_org_required_text_ck",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Site",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=50)),
                ("name", models.CharField(max_length=200)),
                ("is_active", models.BooleanField(default=True)),
                ("deactivated_at", models.DateTimeField(blank=True, null=True)),
                ("deactivation_reason", models.CharField(blank=True, max_length=500)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_site_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "deactivated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_site_deactivated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sites",
                        to="organizations.organization",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_site_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "organizations_site",
                "ordering": ["organization__code", "code"],
                "constraints": [
                    models.UniqueConstraint(
                        models.F("organization"),
                        Lower("code"),
                        name="organizations_site_scope_code_ci_uq",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(
                                ("deactivated_at__isnull", True),
                                ("deactivated_by__isnull", True),
                                ("deactivation_reason", ""),
                                ("is_active", True),
                            )
                            | (
                                models.Q(
                                    ("deactivated_at__isnull", False),
                                    ("deactivated_by__isnull", False),
                                    ("is_active", False),
                                )
                                & ~models.Q(("deactivation_reason", ""))
                            )
                        ),
                        name="organizations_site_lifecycle_ck",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(("code", "")) & ~models.Q(("name", "")),
                        name="organizations_site_required_text_ck",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=50)),
                ("name", models.CharField(max_length=200)),
                ("is_active", models.BooleanField(default=True)),
                ("deactivated_at", models.DateTimeField(blank=True, null=True)),
                ("deactivation_reason", models.CharField(blank=True, max_length=500)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_service_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "deactivated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_service_deactivated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="services",
                        to="organizations.site",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_service_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "organizations_service",
                "ordering": ["site__code", "code"],
                "indexes": [
                    models.Index(
                        fields=["site", "is_active", "code"],
                        name="org_service_catalog_ix",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        models.F("site"),
                        Lower("code"),
                        name="organizations_service_scope_code_ci_uq",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(
                                ("deactivated_at__isnull", True),
                                ("deactivated_by__isnull", True),
                                ("deactivation_reason", ""),
                                ("is_active", True),
                            )
                            | (
                                models.Q(
                                    ("deactivated_at__isnull", False),
                                    ("deactivated_by__isnull", False),
                                    ("is_active", False),
                                )
                                & ~models.Q(("deactivation_reason", ""))
                            )
                        ),
                        name="organizations_service_lifecycle_ck",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(("code", "")) & ~models.Q(("name", "")),
                        name="organizations_service_required_text_ck",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Area",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=50)),
                ("name", models.CharField(max_length=200)),
                ("is_active", models.BooleanField(default=True)),
                ("deactivated_at", models.DateTimeField(blank=True, null=True)),
                ("deactivation_reason", models.CharField(blank=True, max_length=500)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_area_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "deactivated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_area_deactivated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="areas",
                        to="organizations.organization",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="children",
                        to="organizations.area",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_area_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "organizations_area",
                "ordering": ["organization__code", "code"],
                "indexes": [
                    models.Index(
                        fields=["organization", "parent"],
                        name="org_area_hierarchy_ix",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        models.F("organization"),
                        Lower("code"),
                        name="organizations_area_scope_code_ci_uq",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(
                                ("deactivated_at__isnull", True),
                                ("deactivated_by__isnull", True),
                                ("deactivation_reason", ""),
                                ("is_active", True),
                            )
                            | (
                                models.Q(
                                    ("deactivated_at__isnull", False),
                                    ("deactivated_by__isnull", False),
                                    ("is_active", False),
                                )
                                & ~models.Q(("deactivation_reason", ""))
                            )
                        ),
                        name="organizations_area_lifecycle_ck",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(("parent", models.F("id"))),
                        name="organizations_area_not_self_parent_ck",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(("code", "")) & ~models.Q(("name", "")),
                        name="organizations_area_required_text_ck",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ResponsibilityAssignment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "responsibility_type",
                    models.CharField(
                        choices=[
                            ("AREA_OWNER", "Responsable del área"),
                            ("QUALITY_CONTACT", "Contacto de calidad"),
                            ("DATA_STEWARD", "Responsable de datos"),
                            ("BACKUP", "Responsable suplente"),
                        ],
                        max_length=30,
                    ),
                ),
                ("valid_from", models.DateField(default=django.utils.timezone.localdate)),
                ("valid_to", models.DateField(blank=True, null=True)),
                (
                    "area",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="responsibility_assignments",
                        to="organizations.area",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_responsibilityassignment_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organizations_responsibilityassignment_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="organization_responsibilities",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "organizations_responsibility_assignment",
                "ordering": ["area__code", "responsibility_type", "-valid_from"],
                "indexes": [
                    models.Index(
                        fields=["area", "responsibility_type", "valid_from", "valid_to"],
                        name="organizations_resp_current_ix",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("area", "user", "responsibility_type", "valid_from"),
                        name="organizations_resp_start_uq",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(("valid_to__isnull", True))
                            | models.Q(("valid_to__gte", models.F("valid_from")))
                        ),
                        name="organizations_resp_dates_ck",
                    ),
                ],
            },
        ),
    ]
