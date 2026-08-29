from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.auditlog.models import EventResult
from apps.auditlog.services import record_event
from apps.documents.models import FileAsset, ScanStatus
from apps.organizations.models import Service

from .models import (
    ExportConsumer,
    ExportContract,
    ExportContractStatus,
    ExportFormat,
    ExportRun,
)
from .renderers import MAX_RENDER_ROWS, SYNTHETIC_MARKER, render_export
from .schemas import schema_for
from .selectors import ReportFilters, dataset_rows

STATUS_PATTERN = re.compile(r"^[a-z_]{0,40}$")
MEDIA_TYPES: dict[str, str] = {
    str(ExportFormat.CSV): "text/csv",
    str(ExportFormat.XLSX): "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    str(ExportFormat.PDF): "application/pdf",
}


@dataclass(frozen=True)
class ExportArtifact:
    run: ExportRun
    content: bytes
    filename: str
    media_type: str


def _require_export(actor: User) -> None:
    if not actor.is_active or not has_capability(actor, Capability.EXPORT_REPORTS):
        raise PermissionDenied("El actor no cuenta con capacidad para exportar reportes.")


def _require_contract_governance(actor: User) -> None:
    if not actor.is_active or not actor.is_superuser:
        raise PermissionDenied("Solo la administración del sistema gobierna contratos.")


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def schema_hash(schema_definition: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(schema_definition).encode("utf-8")).hexdigest()


def _parse_date(value: object, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationError({field_name: "La fecha debe usar formato AAAA-MM-DD."}) from exc


def _parse_uuid(value: object, field_name: str) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise ValidationError({field_name: "El identificador del filtro no es válido."}) from exc


def parse_report_filters(values: Mapping[str, object]) -> ReportFilters:
    filters = ReportFilters(
        period_start=_parse_date(values.get("period_start"), "period_start"),
        period_end=_parse_date(values.get("period_end"), "period_end"),
        site_id=_parse_uuid(values.get("site_id"), "site_id"),
        service_id=_parse_uuid(values.get("service_id"), "service_id"),
        process_id=_parse_uuid(values.get("process_id"), "process_id"),
        indicator_id=_parse_uuid(values.get("indicator_id"), "indicator_id"),
        status=str(values.get("status") or "").strip(),
    )
    if filters.period_start and filters.period_end and filters.period_end < filters.period_start:
        raise ValidationError("El fin del periodo no puede preceder al inicio.")
    if not STATUS_PATTERN.fullmatch(filters.status):
        raise ValidationError({"status": "El estado del filtro no es válido."})
    if filters.site_id and filters.service_id:
        if not Service.objects.filter(pk=filters.service_id, site_id=filters.site_id).exists():
            raise ValidationError("El servicio debe pertenecer a la sede filtrada.")
    return filters


@transaction.atomic
def create_export_contract(
    *,
    actor: User,
    code: str,
    name: str,
    dataset: str,
    export_format: str,
    consumer: str = ExportConsumer.GENERAL,
    schema_definition: dict[str, Any] | None = None,
) -> ExportContract:
    _require_contract_governance(actor)
    expected_schema = schema_for(dataset)
    definition = schema_definition or expected_schema
    if definition != expected_schema:
        raise ValidationError("El esquema debe corresponder al contrato implementado del conjunto.")
    normalized_code = code.strip().upper()
    latest = (
        ExportContract.objects.select_for_update()
        .filter(code__iexact=normalized_code)
        .aggregate(max_version=Max("version_no"))["max_version"]
        or 0
    )
    contract = ExportContract(
        code=normalized_code,
        version_no=int(latest) + 1,
        name=name.strip(),
        dataset=dataset,
        format=export_format,
        consumer=consumer,
        schema_definition=definition,
        schema_hash=schema_hash(definition),
        created_by=actor,
        updated_by=actor,
    )
    contract.full_clean()
    contract.save()
    record_event(
        actor=actor,
        object_type="reports.ExportContract",
        object_id=contract.pk,
        action="export_contract.created",
        result=EventResult.SUCCESS,
        context={
            "code": contract.code,
            "dataset": contract.dataset,
            "format": contract.format,
            "version_no": contract.version_no,
        },
    )
    return contract


@transaction.atomic
def publish_export_contract(*, actor: User, contract: ExportContract) -> ExportContract:
    _require_contract_governance(actor)
    locked = ExportContract.objects.select_for_update().get(pk=contract.pk)
    if locked.status != ExportContractStatus.DRAFT:
        raise ValidationError("Solo un contrato en borrador puede publicarse.")
    if schema_hash(locked.schema_definition) != locked.schema_hash:
        raise ValidationError("El hash no corresponde al esquema del contrato.")
    if locked.schema_definition != schema_for(locked.dataset):
        raise ValidationError("El contrato no coincide con el esquema implementado.")
    prior = ExportContract.objects.select_for_update().filter(
        code__iexact=locked.code, status=ExportContractStatus.PUBLISHED
    )
    for item in prior:
        item.status = ExportContractStatus.SUPERSEDED
        item.updated_by = actor
        item.full_clean()
        item.save(update_fields=["status", "updated_by", "updated_at"])
    locked.status = ExportContractStatus.PUBLISHED
    locked.published_at = timezone.now()
    locked.published_by = actor
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["status", "published_at", "published_by", "updated_by", "updated_at"]
    )
    record_event(
        actor=actor,
        object_type="reports.ExportContract",
        object_id=locked.pk,
        action="export_contract.published",
        result=EventResult.SUCCESS,
        context={"code": locked.code, "schema_hash": locked.schema_hash},
    )
    return locked


def _decorate_rows(
    *,
    contract: ExportContract,
    rows: list[dict[str, object]],
    filters_json: str,
    generated_at_utc: str,
) -> list[dict[str, object]]:
    metadata = {
        "synthetic_marker": SYNTHETIC_MARKER,
        "contract_code": contract.code,
        "contract_version": contract.version_no,
        "schema_hash": contract.schema_hash,
        "generated_at_utc": generated_at_utc,
        "filters_json": filters_json,
    }
    return [{**metadata, **row} for row in rows]


def _filename(contract: ExportContract, generated_at: str) -> str:
    timestamp = generated_at.replace("-", "").replace(":", "").replace("T", "-")[:15]
    return f"{contract.code.casefold()}-v{contract.version_no}-{timestamp}.{contract.format}"


@transaction.atomic
def generate_export(
    *, actor: User, contract: ExportContract, filters: ReportFilters
) -> ExportArtifact:
    _require_export(actor)
    locked = ExportContract.objects.select_for_update().get(pk=contract.pk)
    if locked.status != ExportContractStatus.PUBLISHED:
        raise ValidationError("Solo un contrato publicado puede generar exportaciones.")
    if locked.schema_definition != schema_for(locked.dataset):
        raise ValidationError("RNF-014: el contrato publicado no coincide con el esquema.")
    raw_rows = dataset_rows(dataset=locked.dataset, filters=filters)
    if len(raw_rows) > MAX_RENDER_ROWS:
        raise ValidationError("La consulta supera el máximo de 10 000 filas.")
    generated_at = timezone.now()
    generated_at_utc = generated_at.isoformat().replace("+00:00", "Z")
    filters_json = canonical_json(filters.as_dict())
    rows = _decorate_rows(
        contract=locked,
        rows=raw_rows,
        filters_json=filters_json,
        generated_at_utc=generated_at_utc,
    )
    columns = locked.schema_definition["columns"]
    content = render_export(
        export_format=locked.format,
        title=locked.name,
        contract_code=locked.code,
        version_no=locked.version_no,
        schema_hash=locked.schema_hash,
        filters_json=filters_json,
        generated_at=generated_at_utc,
        columns=columns,
        rows=rows,
    )
    digest = hashlib.sha256(content).hexdigest()
    filename = _filename(locked, generated_at_utc)
    run_id = uuid.uuid4()
    asset = FileAsset(
        storage_key=f"reports/{run_id}/{filename}",
        original_name=filename,
        media_type=MEDIA_TYPES[locked.format],
        size_bytes=len(content),
        sha256=digest,
        scan_status=ScanStatus.CLEAN,
        synthetic_confirmed=True,
        created_by=actor,
        updated_by=actor,
    )
    asset.full_clean()
    asset.save()
    run = ExportRun(
        id=run_id,
        contract=locked,
        requested_by=actor,
        filters=filters.as_dict(),
        file_asset=asset,
        row_count=len(raw_rows),
        generated_at=generated_at,
        output_hash=digest,
        created_by=actor,
        updated_by=actor,
    )
    run.full_clean()
    run.save()
    record_event(
        actor=actor,
        object_type="reports.ExportRun",
        object_id=run.pk,
        action="report.exported",
        result=EventResult.SUCCESS,
        context={
            "consumer": locked.consumer,
            "contract_code": locked.code,
            "contract_version": locked.version_no,
            "filters": run.filters,
            "format": locked.format,
            "output_hash": digest,
            "row_count": run.row_count,
        },
    )
    return ExportArtifact(
        run=run,
        content=content,
        filename=filename,
        media_type=MEDIA_TYPES[locked.format],
    )
