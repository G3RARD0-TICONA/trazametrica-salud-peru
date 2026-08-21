from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.accounts.services import date_ranges_overlap
from apps.auditlog.models import EventResult
from apps.auditlog.services import record_event
from apps.documents.models import Document
from apps.organizations.models import Area, Organization

from .models import (
    Process,
    ProcessType,
    ProcessVersion,
    ProcessVersionStatus,
    SipocEntry,
    SipocEntryType,
)


def _require(actor: User, capability: Capability) -> None:
    if not actor.is_active or not has_capability(actor, capability):
        raise PermissionDenied("El actor no cuenta con la capacidad de procesos requerida.")


def _require_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized:
        raise ValidationError("La decisión requiere un motivo.")
    return normalized


def process_version_hash(
    *,
    process: Process,
    version_no: int,
    objective: str,
    scope: str,
    entries: list[dict[str, object]],
) -> str:
    payload = {
        "entries": entries,
        "objective": objective.strip(),
        "process_id": str(process.pk),
        "scope": scope.strip(),
        "version_no": version_no,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _entry_payload(version: ProcessVersion) -> list[dict[str, object]]:
    return [
        {
            "description": entry.description.strip(),
            "entry_type": entry.entry_type,
            "name": entry.name.strip(),
            "position": entry.position,
        }
        for entry in version.sipoc_entries.order_by("entry_type", "position", "id")
    ]


def _recalculate_hash(*, actor: User, version: ProcessVersion) -> ProcessVersion:
    version.version_hash = process_version_hash(
        process=version.process,
        version_no=version.version_no,
        objective=version.objective,
        scope=version.scope,
        entries=_entry_payload(version),
    )
    version.updated_by = actor
    version.full_clean()
    version.save(update_fields=["version_hash", "updated_by", "updated_at"])
    return version


@transaction.atomic
def create_process(
    *,
    actor: User,
    organization: Organization,
    owner_area: Area,
    code: str,
    name: str,
    process_type: ProcessType,
) -> Process:
    _require(actor, Capability.DRAFT_PROCESSES)
    if not organization.is_active or not owner_area.is_active:
        raise ValidationError("La organización y el área propietaria deben estar activas.")
    if owner_area.organization_id != organization.pk:
        raise ValidationError("El área propietaria debe pertenecer a la organización.")
    process = Process(
        organization=organization,
        owner_area=owner_area,
        code=code,
        name=name,
        process_type=process_type,
        created_by=actor,
        updated_by=actor,
    )
    process.full_clean()
    process.save()
    record_event(
        actor=actor,
        object_type="processes.Process",
        object_id=process.pk,
        action="process.created",
        result=EventResult.SUCCESS,
        context={"code": process.code, "process_type": process.process_type},
    )
    return process


@transaction.atomic
def update_process_metadata(
    *,
    actor: User,
    process: Process,
    name: str,
    owner_area: Area,
    process_type: ProcessType,
) -> Process:
    _require(actor, Capability.DRAFT_PROCESSES)
    locked = Process.objects.select_for_update().get(pk=process.pk)
    if not locked.is_active:
        raise ValidationError("No se edita un proceso inactivo.")
    if not owner_area.is_active or owner_area.organization_id != locked.organization_id:
        raise ValidationError("El área propietaria activa debe pertenecer a la organización.")
    locked.name = name
    locked.owner_area = owner_area
    locked.process_type = process_type
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["name", "owner_area", "process_type", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="processes.Process",
        object_id=locked.pk,
        action="process.metadata_updated",
        result=EventResult.SUCCESS,
        context={"owner_area_id": str(owner_area.pk), "process_type": process_type},
    )
    return locked


@transaction.atomic
def create_process_version(
    *,
    actor: User,
    process: Process,
    objective: str,
    scope: str,
) -> ProcessVersion:
    _require(actor, Capability.DRAFT_PROCESSES)
    locked_process = Process.objects.select_for_update().get(pk=process.pk)
    if not locked_process.is_active:
        raise ValidationError("El proceso debe estar activo.")
    last_version = locked_process.versions.aggregate(max_no=Max("version_no"))["max_no"] or 0
    version_no = int(last_version) + 1
    version = ProcessVersion(
        process=locked_process,
        version_no=version_no,
        status=ProcessVersionStatus.DRAFT,
        objective=objective,
        scope=scope,
        version_hash=process_version_hash(
            process=locked_process,
            version_no=version_no,
            objective=objective,
            scope=scope,
            entries=[],
        ),
        created_by=actor,
        updated_by=actor,
    )
    version.full_clean()
    version.save()
    record_event(
        actor=actor,
        object_type="processes.ProcessVersion",
        object_id=version.pk,
        action="process_version.created",
        result=EventResult.SUCCESS,
        context={"process_id": str(process.pk), "version_no": version_no},
    )
    return version


@transaction.atomic
def update_process_draft(
    *,
    actor: User,
    version: ProcessVersion,
    objective: str,
    scope: str,
) -> ProcessVersion:
    _require(actor, Capability.DRAFT_PROCESSES)
    locked = ProcessVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != ProcessVersionStatus.DRAFT:
        raise ValidationError("Solo una versión en borrador puede editarse.")
    locked.objective = objective
    locked.scope = scope
    locked.version_hash = process_version_hash(
        process=locked.process,
        version_no=locked.version_no,
        objective=objective,
        scope=scope,
        entries=_entry_payload(locked),
    )
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["objective", "scope", "version_hash", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="processes.ProcessVersion",
        object_id=locked.pk,
        action="process_version.updated",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def add_sipoc_entry(
    *,
    actor: User,
    version: ProcessVersion,
    entry_type: SipocEntryType,
    position: int,
    name: str,
    description: str = "",
) -> SipocEntry:
    _require(actor, Capability.DRAFT_PROCESSES)
    locked_version = ProcessVersion.objects.select_for_update().get(pk=version.pk)
    if locked_version.status != ProcessVersionStatus.DRAFT:
        raise ValidationError("El SIPOC solo se modifica en una versión borrador.")
    entry = SipocEntry(
        process_version=locked_version,
        entry_type=entry_type,
        position=position,
        name=name,
        description=description,
        created_by=actor,
        updated_by=actor,
    )
    entry.full_clean()
    entry.save()
    _recalculate_hash(actor=actor, version=locked_version)
    record_event(
        actor=actor,
        object_type="processes.SipocEntry",
        object_id=entry.pk,
        action="sipoc_entry.created",
        result=EventResult.SUCCESS,
        context={"entry_type": entry.entry_type, "position": entry.position},
    )
    return entry


@transaction.atomic
def update_sipoc_entry(
    *,
    actor: User,
    entry: SipocEntry,
    position: int,
    name: str,
    description: str = "",
) -> SipocEntry:
    _require(actor, Capability.DRAFT_PROCESSES)
    locked = (
        SipocEntry.objects.select_for_update().select_related("process_version").get(pk=entry.pk)
    )
    if locked.process_version.status != ProcessVersionStatus.DRAFT:
        raise ValidationError("El SIPOC aprobado es inmutable.")
    locked.position = position
    locked.name = name
    locked.description = description
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["position", "name", "description", "updated_by", "updated_at"])
    _recalculate_hash(actor=actor, version=locked.process_version)
    record_event(
        actor=actor,
        object_type="processes.SipocEntry",
        object_id=locked.pk,
        action="sipoc_entry.updated",
        result=EventResult.SUCCESS,
        context={"entry_type": locked.entry_type, "position": locked.position},
    )
    return locked


@transaction.atomic
def remove_sipoc_entry(*, actor: User, entry: SipocEntry, reason: str) -> None:
    _require(actor, Capability.DRAFT_PROCESSES)
    normalized_reason = _require_reason(reason)
    locked = (
        SipocEntry.objects.select_for_update().select_related("process_version").get(pk=entry.pk)
    )
    version = locked.process_version
    if version.status != ProcessVersionStatus.DRAFT:
        raise ValidationError("El SIPOC aprobado es inmutable.")
    entry_id = locked.pk
    entry_type = locked.entry_type
    position = locked.position
    locked.delete()
    _recalculate_hash(actor=actor, version=version)
    record_event(
        actor=actor,
        object_type="processes.SipocEntry",
        object_id=entry_id,
        action="sipoc_entry.removed_from_draft",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"entry_type": entry_type, "position": position},
    )


def _validate_complete_sipoc(version: ProcessVersion) -> None:
    observed = set(version.sipoc_entries.values_list("entry_type", flat=True))
    missing = set(SipocEntryType.values) - observed
    if missing:
        labels = dict(SipocEntryType.choices)
        missing_labels = ", ".join(sorted(labels[value] for value in missing))
        raise ValidationError(f"El SIPOC está incompleto: faltan {missing_labels}.")


@transaction.atomic
def submit_process_version(*, actor: User, version: ProcessVersion) -> ProcessVersion:
    _require(actor, Capability.DRAFT_PROCESSES)
    locked = ProcessVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != ProcessVersionStatus.DRAFT:
        raise ValidationError("Solo un borrador puede enviarse a revisión.")
    _validate_complete_sipoc(locked)
    _recalculate_hash(actor=actor, version=locked)
    locked.status = ProcessVersionStatus.IN_REVIEW
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
        object_type="processes.ProcessVersion",
        object_id=locked.pk,
        action="process_version.submitted",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def reject_process_version(
    *,
    actor: User,
    version: ProcessVersion,
    reason: str,
) -> ProcessVersion:
    _require(actor, Capability.REVIEW_PROCESSES)
    normalized_reason = _require_reason(reason)
    locked = ProcessVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != ProcessVersionStatus.IN_REVIEW:
        raise ValidationError("Solo una versión en revisión puede rechazarse.")
    locked.status = ProcessVersionStatus.DRAFT
    locked.reviewed_at = timezone.now()
    locked.reviewed_by = actor
    locked.decision_reason = normalized_reason
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "reviewed_at",
            "reviewed_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="processes.ProcessVersion",
        object_id=locked.pk,
        action="process_version.rejected",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"version_no": locked.version_no},
    )
    return locked


def _supersede_effective_versions(
    *,
    actor: User,
    version: ProcessVersion,
    valid_from: date,
    valid_to: date | None,
) -> None:
    candidates = (
        ProcessVersion.objects.select_for_update()
        .filter(
            process=version.process,
            status__in=[ProcessVersionStatus.APPROVED, ProcessVersionStatus.EFFECTIVE],
        )
        .exclude(pk=version.pk)
    )
    for other in candidates:
        if other.valid_from is None:
            raise ValidationError("La versión aprobada existente carece de inicio de vigencia.")
        if not date_ranges_overlap(other.valid_from, other.valid_to, valid_from, valid_to):
            continue
        if other.status == ProcessVersionStatus.EFFECTIVE and other.valid_from < valid_from:
            other.valid_to = valid_from - timedelta(days=1)
            if valid_from <= timezone.localdate():
                other.status = ProcessVersionStatus.SUPERSEDED
            other.updated_by = actor
            other.save(update_fields=["valid_to", "status", "updated_by", "updated_at"])
            continue
        raise ValidationError("La vigencia propuesta se superpone con otra versión aprobada.")


@transaction.atomic
def approve_process_version(
    *,
    actor: User,
    version: ProcessVersion,
    valid_from: date,
    valid_to: date | None = None,
    reason: str = "",
) -> ProcessVersion:
    _require(actor, Capability.APPROVE_PROCESSES)
    locked = ProcessVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != ProcessVersionStatus.IN_REVIEW:
        raise ValidationError("Solo una versión en revisión puede aprobarse.")
    if locked.created_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propia versión de proceso.")
    if valid_to is not None and valid_to < valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")
    _validate_complete_sipoc(locked)
    _supersede_effective_versions(
        actor=actor,
        version=locked,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    locked.status = (
        ProcessVersionStatus.EFFECTIVE
        if valid_from <= timezone.localdate()
        else ProcessVersionStatus.APPROVED
    )
    locked.valid_from = valid_from
    locked.valid_to = valid_to
    locked.reviewed_at = timezone.now()
    locked.reviewed_by = actor
    locked.approved_at = locked.reviewed_at
    locked.approved_by = actor
    locked.decision_reason = reason.strip()
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "valid_from",
            "valid_to",
            "reviewed_at",
            "reviewed_by",
            "approved_at",
            "approved_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="processes.ProcessVersion",
        object_id=locked.pk,
        action="process_version.approved",
        result=EventResult.SUCCESS,
        reason=locked.decision_reason,
        context={"status": locked.status, "version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def annul_process_version(
    *,
    actor: User,
    version: ProcessVersion,
    reason: str,
) -> ProcessVersion:
    _require(actor, Capability.APPROVE_PROCESSES)
    normalized_reason = _require_reason(reason)
    locked = ProcessVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status in {ProcessVersionStatus.SUPERSEDED, ProcessVersionStatus.ANNULLED}:
        raise ValidationError("La versión ya no admite anulación.")
    today = timezone.localdate()
    if locked.status == ProcessVersionStatus.EFFECTIVE and (
        locked.valid_to is None or locked.valid_to > today
    ):
        locked.valid_to = today
    locked.status = ProcessVersionStatus.ANNULLED
    locked.reviewed_at = timezone.now()
    locked.reviewed_by = actor
    locked.decision_reason = normalized_reason
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "status",
            "valid_to",
            "reviewed_at",
            "reviewed_by",
            "decision_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="processes.ProcessVersion",
        object_id=locked.pk,
        action="process_version.annulled",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def link_document_to_process(
    *,
    actor: User,
    document: Document,
    process: Process | None,
) -> Document:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    if not has_capability(actor, Capability.DRAFT_PROCESSES):
        raise PermissionDenied("Vincular documentos requiere gestión documental y de procesos.")
    locked_document = Document.objects.select_for_update().get(pk=document.pk)
    if not locked_document.is_active:
        raise ValidationError("El documento debe estar activo.")
    if process is not None:
        locked_process = Process.objects.select_for_update().get(pk=process.pk)
        if not locked_process.is_active:
            raise ValidationError("El proceso debe estar activo.")
        if locked_process.organization_id != locked_document.organization_id:
            raise ValidationError("El documento y el proceso deben pertenecer a la organización.")
    else:
        locked_process = None
    locked_document.process = locked_process
    locked_document.updated_by = actor
    locked_document.full_clean()
    locked_document.save(update_fields=["process", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="documents.Document",
        object_id=locked_document.pk,
        action="document.process_link_updated",
        result=EventResult.SUCCESS,
        context={"process_id": str(locked_process.pk) if locked_process else None},
    )
    return locked_document


@transaction.atomic
def deactivate_process(*, actor: User, process: Process, reason: str) -> Process:
    _require(actor, Capability.DRAFT_PROCESSES)
    normalized_reason = _require_reason(reason)
    locked = Process.objects.select_for_update().get(pk=process.pk)
    if not locked.is_active:
        raise ValidationError("El proceso ya está inactivo.")
    open_statuses = [
        ProcessVersionStatus.DRAFT,
        ProcessVersionStatus.IN_REVIEW,
        ProcessVersionStatus.APPROVED,
        ProcessVersionStatus.EFFECTIVE,
    ]
    if locked.versions.filter(status__in=open_statuses).exists():
        raise ValidationError("Anule o sustituya las versiones abiertas antes de desactivar.")
    if locked.documents.filter(is_active=True).exists():
        raise ValidationError("Desvincule los documentos activos antes de desactivar.")
    locked.is_active = False
    locked.deactivated_at = timezone.now()
    locked.deactivated_by = actor
    locked.deactivation_reason = normalized_reason
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "is_active",
            "deactivated_at",
            "deactivated_by",
            "deactivation_reason",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="processes.Process",
        object_id=locked.pk,
        action="process.deactivated",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
    )
    return locked
