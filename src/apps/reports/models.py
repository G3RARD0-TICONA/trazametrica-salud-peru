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

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ProtectedReportQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError("Los contratos y exportaciones se modifican mediante servicios.")

    def delete(self) -> NoReturn:
        raise ValidationError("La evidencia de exportación no se elimina físicamente.")


class AuditedReportRecord(models.Model):
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
    objects: ClassVar[models.Manager[Any]] = ProtectedReportQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError("La evidencia de exportación no se elimina físicamente.")


class ExportContractStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    PUBLISHED = "published", "Publicado"
    SUPERSEDED = "superseded", "Sustituido"
    ANNULLED = "annulled", "Anulado"


class ExportFormat(models.TextChoices):
    CSV = "csv", "CSV UTF-8"
    XLSX = "xlsx", "Excel XLSX"
    PDF = "pdf", "PDF"


class ExportConsumer(models.TextChoices):
    GENERAL = "general", "Consulta general"
    POWER_BI_DESKTOP = "power_bi_desktop", "Power BI Desktop"


class DatasetCode(models.TextChoices):
    DASHBOARD = "dashboard", "Tablero de indicadores"
    INDICATOR_RESULTS = "indicator_results", "Resultados KPI"
    RISKS = "risks", "Riesgos y controles"
    FINDINGS = "findings", "Hallazgos"
    CORRECTIVE_ACTIONS = "corrective_actions", "Acciones correctivas"


class ExportContract(AuditedReportRecord):
    code = models.CharField(max_length=50)
    version_no = models.PositiveIntegerField()
    name = models.CharField(max_length=200)
    dataset = models.CharField(max_length=40, choices=DatasetCode.choices)
    format = models.CharField(max_length=10, choices=ExportFormat.choices)
    consumer = models.CharField(
        max_length=30,
        choices=ExportConsumer.choices,
        default=ExportConsumer.GENERAL,
    )
    schema_definition = models.JSONField()
    schema_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20,
        choices=ExportContractStatus.choices,
        default=ExportContractStatus.DRAFT,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="export_contracts_published",
    )

    class Meta:
        db_table = "reports_export_contract"
        ordering = ["code", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                Lower("code"), F("version_no"), name="report_contract_code_version_ci_uq"
            ),
            models.CheckConstraint(
                condition=Q(version_no__gte=1), name="report_contract_version_ck"
            ),
            models.CheckConstraint(
                condition=Q(status__in=ExportContractStatus.values),
                name="report_contract_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(dataset__in=DatasetCode.values), name="report_contract_dataset_ck"
            ),
            models.CheckConstraint(
                condition=Q(format__in=ExportFormat.values), name="report_contract_format_ck"
            ),
            models.CheckConstraint(
                condition=Q(consumer__in=ExportConsumer.values),
                name="report_contract_consumer_ck",
            ),
            models.CheckConstraint(
                condition=Q(schema_hash__regex=r"^[0-9a-f]{64}$"),
                name="report_contract_hash_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status=ExportContractStatus.PUBLISHED,
                        published_at__isnull=False,
                        published_by__isnull=False,
                    )
                    | ~Q(status=ExportContractStatus.PUBLISHED)
                ),
                name="report_contract_publication_ck",
            ),
            models.CheckConstraint(
                condition=~Q(code="") & ~Q(name=""), name="report_contract_text_ck"
            ),
        ]
        indexes = [
            models.Index(fields=["status", "dataset", "format"], name="report_contract_catalog_ix")
        ]

    def __str__(self) -> str:
        return f"{self.code} v{self.version_no} — {self.get_format_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            immutable = (
                "code",
                "version_no",
                "name",
                "dataset",
                "format",
                "consumer",
                "schema_definition",
                "schema_hash",
            )
            if original.status != ExportContractStatus.DRAFT and any(
                getattr(original, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError("Un contrato publicado o sustituido es inmutable.")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if not SHA256_PATTERN.fullmatch(self.schema_hash):
            raise ValidationError({"schema_hash": "El hash del esquema no es SHA-256."})
        if not isinstance(self.schema_definition, dict):
            raise ValidationError({"schema_definition": "El esquema debe ser un objeto JSON."})
        columns = self.schema_definition.get("columns")
        if not isinstance(columns, list) or not columns:
            raise ValidationError({"schema_definition": "El esquema requiere columnas."})
        names: list[str] = []
        for column in columns:
            if not isinstance(column, dict):
                raise ValidationError({"schema_definition": "Cada columna debe ser un objeto."})
            name = column.get("name")
            data_type = column.get("type")
            if not isinstance(name, str) or not name.strip():
                raise ValidationError({"schema_definition": "Cada columna requiere nombre."})
            if data_type not in {"text", "integer", "decimal", "date", "datetime", "boolean"}:
                raise ValidationError({"schema_definition": "Existe un tipo de columna inválido."})
            names.append(name)
        if len(names) != len(set(names)):
            raise ValidationError({"schema_definition": "Las columnas no pueden repetirse."})
        if self.consumer == ExportConsumer.POWER_BI_DESKTOP and self.format != ExportFormat.CSV:
            raise ValidationError("Power BI Desktop consume el contrato tabular CSV estable.")
        publication_complete = self.published_at is not None and self.published_by_id is not None
        if (self.published_at is None) != (self.published_by_id is None):
            raise ValidationError("La publicación requiere fecha y publicador.")
        if self.status == ExportContractStatus.PUBLISHED and not publication_complete:
            raise ValidationError("Un contrato publicado debe conservar su publicación.")


class ExportRun(AuditedReportRecord):
    contract = models.ForeignKey(ExportContract, on_delete=models.PROTECT, related_name="runs")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_exports",
    )
    filters = models.JSONField(default=dict, blank=True)
    file_asset = models.ForeignKey(FileAsset, on_delete=models.PROTECT, related_name="export_runs")
    row_count = models.PositiveIntegerField()
    generated_at = models.DateTimeField()
    output_hash = models.CharField(max_length=64)

    class Meta:
        db_table = "reports_export_run"
        ordering = ["-generated_at"]
        constraints = [
            models.CheckConstraint(condition=Q(row_count__gte=0), name="report_run_rows_ck"),
            models.CheckConstraint(
                condition=Q(output_hash__regex=r"^[0-9a-f]{64}$"),
                name="report_run_hash_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["requested_by", "-generated_at"], name="report_run_requester_ix"),
            models.Index(fields=["contract", "-generated_at"], name="report_run_contract_ix"),
        ]

    def __str__(self) -> str:
        return f"{self.contract.code} — {self.generated_at.isoformat()}"

    def clean(self) -> None:
        super().clean()
        if not SHA256_PATTERN.fullmatch(self.output_hash):
            raise ValidationError({"output_hash": "El hash de salida no es SHA-256."})
        if not isinstance(self.filters, dict):
            raise ValidationError({"filters": "Los filtros deben ser un objeto JSON."})
        if self.requested_by_id != self.created_by_id:
            raise ValidationError("El solicitante debe corresponder al autor de la exportación.")
        if self.file_asset.sha256 != self.output_hash:
            raise ValidationError("El archivo y la ejecución deben conservar el mismo hash.")
        if self.file_asset.synthetic_confirmed is not True:
            raise ValidationError("La exportación debe estar marcada como sintética.")
