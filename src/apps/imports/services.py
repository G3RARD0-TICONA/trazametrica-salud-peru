from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import PurePath
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
from apps.organizations.models import Organization

from .models import (
    ImportError,
    ImportErrorSeverity,
    ImportJob,
    ImportJobStatus,
    ImportRow,
    ImportTemplate,
    ImportTemplateVersion,
    TemplateTargetType,
    TemplateVersionStatus,
)
from .xlsx import (
    MAX_XLSX_BYTES,
    ParsedWorkbook,
    XlsxValidationError,
    generate_workbook,
    parse_workbook,
)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ALLOWED_COLUMN_TYPES = frozenset({"string", "integer", "decimal", "date", "boolean"})
COLUMN_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,99}$")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.IGNORECASE)
FORBIDDEN_PERSONAL_COLUMNS = frozenset(
    {
        "dni",
        "documento_identidad",
        "historia_clinica",
        "nombre_paciente",
        "diagnostico",
        "telefono",
        "correo_personal",
    }
)


def _require(actor: User, capability: Capability) -> None:
    if not actor.is_active or not has_capability(actor, capability):
        raise PermissionDenied("El actor no cuenta con la capacidad de importación requerida.")


def _require_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized:
        raise ValidationError("La decisión requiere un motivo.")
    return normalized


def normalize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, dict):
        raise ValidationError("El esquema debe ser un objeto JSON.")
    columns = schema.get("columns")
    if not isinstance(columns, list) or not 1 <= len(columns) <= 100:
        raise ValidationError("El esquema requiere entre 1 y 100 columnas.")
    normalized_columns: list[dict[str, Any]] = []
    observed: set[str] = set()
    for position, raw_column in enumerate(columns, start=1):
        if not isinstance(raw_column, dict):
            raise ValidationError(f"La columna {position} no posee una definición válida.")
        name = str(raw_column.get("name", "")).strip().casefold()
        column_type = str(raw_column.get("type", "")).strip().casefold()
        if not COLUMN_NAME_PATTERN.fullmatch(name):
            raise ValidationError(f"El nombre de columna {name!r} no es válido.")
        if name in observed:
            raise ValidationError(f"La columna {name} está duplicada.")
        if name in FORBIDDEN_PERSONAL_COLUMNS:
            raise ValidationError(f"La columna {name} puede contener datos personales o clínicos.")
        if column_type not in ALLOWED_COLUMN_TYPES:
            raise ValidationError(f"El tipo de {name} no está permitido.")
        normalized: dict[str, Any] = {
            "name": name,
            "type": column_type,
            "required": bool(raw_column.get("required", False)),
        }
        if "max_length" in raw_column:
            max_length = int(raw_column["max_length"])
            if column_type != "string" or not 1 <= max_length <= 500:
                raise ValidationError(f"max_length de {name} no es válido.")
            normalized["max_length"] = max_length
        if "pattern" in raw_column:
            pattern = str(raw_column["pattern"])
            if column_type != "string" or len(pattern) > 200:
                raise ValidationError(f"pattern de {name} no es válido.")
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValidationError(f"pattern de {name} no compila.") from exc
            normalized["pattern"] = pattern
        if "choices" in raw_column:
            choices = raw_column["choices"]
            if not isinstance(choices, list) or not choices or len(choices) > 100:
                raise ValidationError(f"choices de {name} no es válido.")
            normalized["choices"] = [str(choice).strip() for choice in choices]
        for bound in ("min", "max"):
            if bound in raw_column:
                if column_type not in {"integer", "decimal"}:
                    raise ValidationError(f"{bound} de {name} requiere tipo numérico.")
                try:
                    normalized[bound] = str(Decimal(str(raw_column[bound])))
                except InvalidOperation as exc:
                    raise ValidationError(f"{bound} de {name} no es numérico.") from exc
        if "min" in normalized and "max" in normalized:
            if Decimal(normalized["min"]) > Decimal(normalized["max"]):
                raise ValidationError(f"El rango de {name} está invertido.")
        if column_type == "date":
            normalized["allow_future"] = bool(raw_column.get("allow_future", False))
        normalized["unique_in_file"] = bool(raw_column.get("unique_in_file", False))
        observed.add(name)
        normalized_columns.append(normalized)
    return {
        "sheet_name": "DATOS",
        "synthetic_marker": "DATOS SINTÉTICOS",
        "columns": normalized_columns,
    }


def schema_hash(schema: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(schema, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


@transaction.atomic
def create_import_template(
    *,
    actor: User,
    organization: Organization,
    code: str,
    name: str,
    target_type: TemplateTargetType,
) -> ImportTemplate:
    _require(actor, Capability.CREATE_IMPORTS)
    if not organization.is_active:
        raise ValidationError("La organización debe estar activa.")
    template = ImportTemplate(
        organization=organization,
        code=code,
        name=name,
        target_type=target_type,
        created_by=actor,
        updated_by=actor,
    )
    template.full_clean()
    template.save()
    record_event(
        actor=actor,
        object_type="imports.ImportTemplate",
        object_id=template.pk,
        action="import_template.created",
        result=EventResult.SUCCESS,
        context={"code": template.code, "target_type": template.target_type},
    )
    return template


@transaction.atomic
def create_template_version(
    *,
    actor: User,
    template: ImportTemplate,
    schema_definition: dict[str, Any],
) -> ImportTemplateVersion:
    _require(actor, Capability.CREATE_IMPORTS)
    locked_template = ImportTemplate.objects.select_for_update().get(pk=template.pk)
    if not locked_template.is_active:
        raise ValidationError("La plantilla debe estar activa.")
    normalized = normalize_schema(schema_definition)
    max_version = locked_template.versions.aggregate(max_no=Max("version_no"))["max_no"] or 0
    version = ImportTemplateVersion(
        template=locked_template,
        version_no=int(max_version) + 1,
        status=TemplateVersionStatus.DRAFT,
        schema_definition=normalized,
        schema_hash=schema_hash(normalized),
        created_by=actor,
        updated_by=actor,
    )
    version.full_clean()
    version.save()
    record_event(
        actor=actor,
        object_type="imports.ImportTemplateVersion",
        object_id=version.pk,
        action="import_template_version.created",
        result=EventResult.SUCCESS,
        context={"template_id": str(template.pk), "version_no": version.version_no},
    )
    return version


@transaction.atomic
def submit_template_version(
    *, actor: User, version: ImportTemplateVersion
) -> ImportTemplateVersion:
    _require(actor, Capability.CREATE_IMPORTS)
    locked = ImportTemplateVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != TemplateVersionStatus.DRAFT:
        raise ValidationError("Solo una plantilla borrador puede enviarse a revisión.")
    normalize_schema(locked.schema_definition)
    locked.status = TemplateVersionStatus.IN_REVIEW
    locked.submitted_at = timezone.now()
    locked.submitted_by = actor
    locked.decision_reason = ""
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "submitted_at",
            "submitted_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="imports.ImportTemplateVersion",
        object_id=locked.pk,
        action="import_template_version.submitted",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def approve_template_version(
    *,
    actor: User,
    version: ImportTemplateVersion,
    valid_from: date,
    valid_to: date | None = None,
    reason: str = "",
) -> ImportTemplateVersion:
    _require(actor, Capability.APPROVE_IMPORTS)
    locked = ImportTemplateVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != TemplateVersionStatus.IN_REVIEW:
        raise ValidationError("Solo una plantilla en revisión puede aprobarse.")
    if locked.created_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propia plantilla.")
    today = timezone.localdate()
    if valid_from > today:
        raise ValidationError("Una plantilla publicada debe iniciar vigencia hoy o antes.")
    if valid_to is not None and valid_to < valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")
    previous = (
        ImportTemplateVersion.objects.select_for_update()
        .filter(template=locked.template, status=TemplateVersionStatus.EFFECTIVE)
        .exclude(pk=locked.pk)
    )
    for other in previous:
        if other.valid_from is None:
            raise ValidationError("La plantilla vigente anterior carece de fecha inicial.")
        other.valid_to = max(other.valid_from, valid_from - timedelta(days=1))
        other.status = TemplateVersionStatus.SUPERSEDED
        other.updated_by = actor
        other.save(update_fields=["valid_to", "status", "updated_by", "updated_at"])
    locked.status = TemplateVersionStatus.EFFECTIVE
    locked.valid_from = valid_from
    locked.valid_to = valid_to
    locked.approved_at = timezone.now()
    locked.approved_by = actor
    locked.decision_reason = reason.strip()
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "valid_from",
            "valid_to",
            "approved_at",
            "approved_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="imports.ImportTemplateVersion",
        object_id=locked.pk,
        action="import_template_version.approved",
        result=EventResult.SUCCESS,
        reason=locked.decision_reason,
        context={"version_no": locked.version_no},
    )
    return locked


def template_workbook(version: ImportTemplateVersion) -> bytes:
    if version.status != TemplateVersionStatus.EFFECTIVE:
        raise ValidationError("Solo puede descargarse una plantilla vigente.")
    today = timezone.localdate()
    if version.valid_from is None or version.valid_from > today:
        raise ValidationError("La plantilla todavía no está vigente.")
    if version.valid_to is not None and version.valid_to < today:
        raise ValidationError("La plantilla ya no está vigente.")
    return generate_workbook(
        template_code=version.template.code,
        version_no=version.version_no,
        schema_hash=version.schema_hash,
        schema=version.schema_definition,
    )


def _register_import_asset(
    *, actor: User, original_name: str, content: bytes, digest: str
) -> FileAsset:
    asset = FileAsset(
        storage_key=f"imports/{uuid.uuid4()}.xlsx",
        original_name=original_name,
        media_type=XLSX_MEDIA_TYPE,
        size_bytes=len(content),
        sha256=digest,
        scan_status=ScanStatus.CLEAN,
        synthetic_confirmed=True,
        created_by=actor,
        updated_by=actor,
    )
    asset.full_clean()
    asset.save()
    record_event(
        actor=actor,
        object_type="documents.FileAsset",
        object_id=asset.pk,
        action="import_file_asset.registered",
        result=EventResult.SUCCESS,
        context={"media_type": XLSX_MEDIA_TYPE, "size_bytes": len(content)},
    )
    return asset


def _row_hash(data: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def _unsafe_email(value: str) -> bool:
    return any(
        not match.group(1).casefold().endswith(".invalid")
        for match in EMAIL_PATTERN.finditer(value)
    )


def _normalize_value(value: str | None, column: dict[str, Any]) -> tuple[object | None, list[str]]:
    errors: list[str] = []
    text = "" if value is None else value.strip()
    if not text:
        if column["required"]:
            errors.append("required")
        return None, errors
    if _unsafe_email(text):
        errors.append("unsafe_real_data")
    column_type = column["type"]
    normalized: object
    if column_type == "string":
        normalized = text
        if len(text) > column.get("max_length", 500):
            errors.append("max_length")
        pattern = column.get("pattern")
        if pattern and re.fullmatch(pattern, text) is None:
            errors.append("pattern")
    elif column_type == "integer":
        try:
            normalized = int(text)
        except ValueError:
            return None, [*errors, "type_integer"]
    elif column_type == "decimal":
        try:
            normalized = str(Decimal(text))
        except InvalidOperation:
            return None, [*errors, "type_decimal"]
    elif column_type == "date":
        try:
            parsed = date.fromisoformat(text)
        except ValueError:
            return None, [*errors, "type_date"]
        normalized = parsed.isoformat()
        if not column.get("allow_future", False) and parsed > timezone.localdate():
            errors.append("future_date")
    else:
        lowered = text.casefold()
        if lowered in {"true", "1", "sí", "si"}:
            normalized = True
        elif lowered in {"false", "0", "no"}:
            normalized = False
        else:
            return None, [*errors, "type_boolean"]
    choices = column.get("choices")
    if choices and str(normalized) not in choices:
        errors.append("choice")
    if column_type in {"integer", "decimal"} and normalized is not None:
        numeric = Decimal(str(normalized))
        if "min" in column and numeric < Decimal(column["min"]):
            errors.append("min")
        if "max" in column and numeric > Decimal(column["max"]):
            errors.append("max")
    return normalized, errors


ERROR_MESSAGES: dict[str, tuple[str, str]] = {
    "required": ("El campo obligatorio está vacío.", "Complete el valor requerido."),
    "unsafe_real_data": (
        "El valor puede contener información real.",
        "Use exclusivamente identificadores o dominios .invalid sintéticos.",
    ),
    "max_length": ("El texto supera la longitud permitida.", "Reduzca el contenido."),
    "pattern": ("El código no cumple el patrón.", "Corrija el formato indicado."),
    "type_integer": ("El valor no es un entero.", "Ingrese un número entero."),
    "type_decimal": ("El valor no es decimal.", "Ingrese un número decimal con punto."),
    "type_date": ("La fecha no usa formato ISO.", "Use AAAA-MM-DD como texto."),
    "future_date": ("La fecha futura no está permitida.", "Use una fecha actual o anterior."),
    "type_boolean": ("El valor no es booleano.", "Use sí/no, true/false o 1/0."),
    "choice": ("El valor no pertenece al catálogo.", "Use una opción publicada."),
    "min": ("El valor es menor al mínimo.", "Ajuste el valor al rango permitido."),
    "max": ("El valor supera el máximo.", "Ajuste el valor al rango permitido."),
    "formula_not_allowed": (
        "Las fórmulas Excel están prohibidas.",
        "Pegue únicamente valores sintéticos.",
    ),
    "duplicate_row": ("La fila está duplicada.", "Elimine la repetición."),
    "duplicate_value": ("El valor debe ser único en el archivo.", "Use un código diferente."),
    "extra_columns": ("La fila contiene columnas adicionales.", "Respete la plantilla publicada."),
}


def _global_rejection(*, job: ImportJob, rule: str, message: str, suggestion: str) -> ImportJob:
    evidence_row = ImportRow.objects.create(
        import_job=job,
        row_number=0,
        raw_data={},
        normalized_hash=_row_hash({}),
        is_valid=False,
    )
    ImportError.objects.create(
        import_row=evidence_row,
        column_name="",
        rule_code=rule,
        severity=ImportErrorSeverity.BLOCKING,
        message=message,
        suggested_action=suggestion,
    )
    job.status = ImportJobStatus.REJECTED
    job.error_count = 1
    job.finished_at = timezone.now()
    job.updated_by = job.created_by
    job.save(update_fields=["status", "error_count", "finished_at", "updated_by", "updated_at"])
    return job


def _validate_workbook(*, job: ImportJob, workbook: ParsedWorkbook) -> ImportJob:
    version = job.template_version
    expected_headers = tuple(column["name"] for column in version.schema_definition["columns"])
    if workbook.marker != "DATOS SINTÉTICOS":
        return _global_rejection(
            job=job,
            rule="synthetic_marker",
            message="La marca DATOS SINTÉTICOS no está presente.",
            suggestion="Descargue nuevamente la plantilla oficial.",
        )
    if (
        workbook.template_code != version.template.code
        or workbook.version_no != version.version_no
        or workbook.schema_hash != version.schema_hash
    ):
        return _global_rejection(
            job=job,
            rule="template_identity",
            message="La identidad de la plantilla no coincide con la versión seleccionada.",
            suggestion="Use la plantilla vigente sin alterar la hoja META.",
        )
    if workbook.headers != expected_headers:
        return _global_rejection(
            job=job,
            rule="headers",
            message="Los encabezados o su orden no coinciden con el esquema.",
            suggestion="No agregue, elimine ni renombre columnas.",
        )
    if not workbook.rows:
        return _global_rejection(
            job=job,
            rule="empty_dataset",
            message="La plantilla no contiene filas de datos.",
            suggestion="Agregue al menos una fila sintética.",
        )

    row_objects: list[ImportRow] = []
    pending_errors: list[tuple[ImportRow, str, str]] = []
    observed_hashes: set[str] = set()
    unique_values: dict[str, set[str]] = {
        column["name"]: set()
        for column in version.schema_definition["columns"]
        if column.get("unique_in_file")
    }
    for workbook_row in workbook.rows:
        normalized_data: dict[str, object] = {}
        row_errors: list[tuple[str, str]] = []
        if len(workbook_row.cells) > len(expected_headers):
            row_errors.append(("", "extra_columns"))
        for index, column in enumerate(version.schema_definition["columns"]):
            cell = workbook_row.cells[index] if index < len(workbook_row.cells) else None
            if cell is not None and cell.formula:
                normalized = None
                rules = ["formula_not_allowed"]
            else:
                normalized, rules = _normalize_value(cell.value if cell else None, column)
            normalized_data[column["name"]] = normalized
            row_errors.extend((column["name"], rule) for rule in rules)
            if column["name"] in unique_values and normalized is not None:
                unique_key = str(normalized)
                if unique_key in unique_values[column["name"]]:
                    row_errors.append((column["name"], "duplicate_value"))
                unique_values[column["name"]].add(unique_key)
        normalized_hash = _row_hash(normalized_data)
        if normalized_hash in observed_hashes:
            row_errors.append(("", "duplicate_row"))
        observed_hashes.add(normalized_hash)
        row_object = ImportRow(
            import_job=job,
            row_number=workbook_row.row_number,
            raw_data=normalized_data,
            normalized_hash=normalized_hash,
            is_valid=not row_errors,
        )
        row_objects.append(row_object)
        pending_errors.extend((row_object, column_name, rule) for column_name, rule in row_errors)
    ImportRow.objects.bulk_create(row_objects, batch_size=1000)
    error_objects = []
    for row, column_name, rule in pending_errors:
        message, suggestion = ERROR_MESSAGES[rule]
        error_objects.append(
            ImportError(
                import_row=row,
                column_name=column_name,
                rule_code=rule,
                severity=ImportErrorSeverity.BLOCKING,
                message=message,
                suggested_action=suggestion,
            )
        )
    if error_objects:
        ImportError.objects.bulk_create(error_objects, batch_size=1000)
    job.row_count = len(row_objects)
    job.error_count = len(error_objects)
    job.status = ImportJobStatus.REJECTED if error_objects else ImportJobStatus.ACCEPTED
    job.finished_at = timezone.now()
    job.updated_by = job.created_by
    job.full_clean()
    job.save(
        update_fields=[
            "row_count",
            "error_count",
            "status",
            "finished_at",
            "updated_by",
            "updated_at",
        ]
    )
    return job


@transaction.atomic
def receive_and_validate_import(
    *,
    actor: User,
    organization: Organization,
    template_version: ImportTemplateVersion,
    original_name: str,
    content: bytes,
    synthetic_confirmed: bool,
    retry_of: ImportJob | None = None,
) -> ImportJob:
    _require(actor, Capability.CREATE_IMPORTS)
    if not synthetic_confirmed:
        raise ValidationError("Debe confirmar que el archivo contiene solo datos sintéticos.")
    if (
        PurePath(original_name).name != original_name
        or PurePath(original_name).suffix.lower() != ".xlsx"
    ):
        raise ValidationError("El archivo debe tener un nombre seguro y extensión .xlsx.")
    if not content or len(content) > MAX_XLSX_BYTES:
        raise ValidationError("El archivo está vacío o supera el límite de 10 MiB.")
    locked_version = (
        ImportTemplateVersion.objects.select_for_update()
        .select_related("template")
        .get(pk=template_version.pk)
    )
    if locked_version.status != TemplateVersionStatus.EFFECTIVE:
        raise ValidationError("La versión de plantilla debe estar vigente.")
    if locked_version.template.organization_id != organization.pk or not organization.is_active:
        raise ValidationError("La plantilla debe pertenecer a la organización activa.")
    if retry_of is not None:
        locked_retry = ImportJob.objects.select_for_update().get(pk=retry_of.pk)
        if locked_retry.organization_id != organization.pk:
            raise ValidationError("El reintento debe pertenecer a la misma organización.")
        if locked_retry.status not in {ImportJobStatus.REJECTED, ImportJobStatus.FAILED}:
            raise ValidationError("Solo una carga rechazada o fallida admite reintento.")
        attempt_count = locked_retry.attempt_count + 1
    else:
        locked_retry = None
        attempt_count = 1
    digest = hashlib.sha256(content).hexdigest()
    source_file = _register_import_asset(
        actor=actor,
        original_name=original_name,
        content=content,
        digest=digest,
    )
    previous = (
        ImportJob.objects.filter(
            organization=organization,
            file_hash=digest,
            status__in=[ImportJobStatus.ACCEPTED, ImportJobStatus.PROCESSED],
        )
        .order_by("created_at")
        .first()
    )
    job = ImportJob(
        template_version=locked_version,
        source_file=source_file,
        organization=organization,
        status=ImportJobStatus.RECEIVED,
        file_hash=digest,
        attempt_count=attempt_count,
        duplicate_of=previous,
        retry_of=locked_retry,
        created_by=actor,
        updated_by=actor,
    )
    job.full_clean()
    job.save()
    if previous is not None:
        job.status = ImportJobStatus.DUPLICATE
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "finished_at", "updated_at"])
        record_event(
            actor=actor,
            object_type="imports.ImportJob",
            object_id=job.pk,
            action="import_job.duplicate",
            result=EventResult.SUCCESS,
            context={"duplicate_of": str(previous.pk), "file_hash": digest},
        )
        return job
    job.status = ImportJobStatus.VALIDATING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at", "updated_at"])
    try:
        workbook = parse_workbook(content)
    except XlsxValidationError as exc:
        job = _global_rejection(
            job=job,
            rule="xlsx_structure",
            message=str(exc),
            suggestion="Use la plantilla vigente y un archivo XLSX seguro.",
        )
    else:
        job = _validate_workbook(job=job, workbook=workbook)
    record_event(
        actor=actor,
        object_type="imports.ImportJob",
        object_id=job.pk,
        action="import_job.validated",
        result=EventResult.SUCCESS,
        context={
            "attempt_count": job.attempt_count,
            "error_count": job.error_count,
            "row_count": job.row_count,
            "status": job.status,
        },
    )
    return job


@transaction.atomic
def promote_import_job(*, actor: User, job: ImportJob) -> ImportJob:
    _require(actor, Capability.REVIEW_IMPORTS)
    locked = ImportJob.objects.select_for_update().get(pk=job.pk)
    if locked.status != ImportJobStatus.ACCEPTED:
        raise ValidationError("Solo una carga aceptada puede procesarse.")
    if locked.error_count or locked.rows.filter(is_valid=False).exists():
        raise ValidationError("Una carga con errores no puede procesarse.")
    locked.status = ImportJobStatus.PROCESSED
    locked.promoted_at = timezone.now()
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["status", "promoted_at", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="imports.ImportJob",
        object_id=locked.pk,
        action="import_job.processed",
        result=EventResult.SUCCESS,
        context={
            "row_count": locked.row_count,
            "template_version_id": str(locked.template_version_id),
        },
    )
    return locked
