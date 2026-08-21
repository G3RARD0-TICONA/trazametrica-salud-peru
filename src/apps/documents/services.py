from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.accounts.services import date_ranges_overlap
from apps.auditlog.models import EventResult
from apps.auditlog.services import record_event
from apps.organizations.models import Area, Organization

from .models import (
    Document,
    DocumentType,
    DocumentVersion,
    FileAsset,
    ReferenceSource,
    ReferenceType,
    ReferenceVersion,
    ScanStatus,
    VersionStatus,
)

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024
FORBIDDEN_COMPLIANCE_CLAIMS = (
    "acreditado por",
    "autorizado por",
    "certificado por",
    "cumple plenamente",
    "garantiza el cumplimiento",
)


def _require(actor: User, capability: Capability) -> None:
    if not actor.is_active or not has_capability(actor, capability):
        raise PermissionDenied("El actor no cuenta con la capacidad documental requerida.")


def _require_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized:
        raise ValidationError("La decisión requiere un motivo.")
    return normalized


def _validate_no_compliance_claims(*values: str) -> None:
    text = " ".join(values).casefold()
    if any(claim in text for claim in FORBIDDEN_COMPLIANCE_CLAIMS):
        raise ValidationError(
            "La referencia puede describir requisitos, pero no declarar certificación "
            "o cumplimiento."
        )


def _payload_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def document_version_hash(
    *,
    document: Document,
    version_no: int,
    content: str,
    file_asset: FileAsset | None,
) -> str:
    return _payload_hash(
        {
            "document_id": str(document.pk),
            "file_sha256": file_asset.sha256 if file_asset else None,
            "normalized_content": content.strip(),
            "version_no": version_no,
        }
    )


@transaction.atomic
def register_file_asset(
    *,
    actor: User,
    storage_key: str,
    original_name: str,
    media_type: str,
    size_bytes: int,
    sha256: str,
    scan_status: ScanStatus,
    synthetic_confirmed: bool,
) -> FileAsset:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    if size_bytes > MAX_DOCUMENT_SIZE_BYTES:
        raise ValidationError("El archivo supera el límite documental de 10 MiB.")
    asset = FileAsset(
        storage_key=storage_key,
        original_name=original_name,
        media_type=media_type,
        size_bytes=size_bytes,
        sha256=sha256.casefold(),
        scan_status=scan_status,
        synthetic_confirmed=synthetic_confirmed,
        created_by=actor,
        updated_by=actor,
    )
    asset.full_clean()
    asset.save()
    record_event(
        actor=actor,
        object_type="documents.FileAsset",
        object_id=asset.pk,
        action="file_asset.registered",
        result=EventResult.SUCCESS,
        context={"media_type": asset.media_type, "scan_status": asset.scan_status},
    )
    return asset


@transaction.atomic
def create_document(
    *,
    actor: User,
    organization: Organization,
    responsible_area: Area,
    code: str,
    title: str,
    document_type: DocumentType,
) -> Document:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    if not organization.is_active or not responsible_area.is_active:
        raise ValidationError("La organización y el área responsable deben estar activas.")
    if responsible_area.organization_id != organization.pk:
        raise ValidationError("El área responsable debe pertenecer a la organización.")
    document = Document(
        organization=organization,
        responsible_area=responsible_area,
        code=code,
        title=title,
        document_type=document_type,
        created_by=actor,
        updated_by=actor,
    )
    document.full_clean()
    document.save()
    record_event(
        actor=actor,
        object_type="documents.Document",
        object_id=document.pk,
        action="document.created",
        result=EventResult.SUCCESS,
        context={"code": document.code, "document_type": document.document_type},
    )
    return document


@transaction.atomic
def update_document_metadata(
    *,
    actor: User,
    document: Document,
    title: str,
    responsible_area: Area,
) -> Document:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    locked = Document.objects.select_for_update().get(pk=document.pk)
    if not locked.is_active:
        raise ValidationError("No se edita un documento inactivo.")
    if not responsible_area.is_active or responsible_area.organization_id != locked.organization_id:
        raise ValidationError("El área responsable activa debe pertenecer a la organización.")
    locked.title = title
    locked.responsible_area = responsible_area
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["title", "responsible_area", "updated_by", "updated_at"])
    record_event(
        actor=actor,
        object_type="documents.Document",
        object_id=locked.pk,
        action="document.metadata_updated",
        result=EventResult.SUCCESS,
        context={"responsible_area_id": str(responsible_area.pk)},
    )
    return locked


@transaction.atomic
def create_document_version(
    *,
    actor: User,
    document: Document,
    content: str = "",
    file_asset: FileAsset | None = None,
) -> DocumentVersion:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    locked_document = Document.objects.select_for_update().get(pk=document.pk)
    if not locked_document.is_active:
        raise ValidationError("El documento debe estar activo.")
    last_version = locked_document.versions.aggregate(max_no=Max("version_no"))["max_no"] or 0
    version_no = int(last_version) + 1
    version = DocumentVersion(
        document=locked_document,
        version_no=version_no,
        status=VersionStatus.DRAFT,
        content=content,
        file_asset=file_asset,
        version_hash=document_version_hash(
            document=locked_document,
            version_no=version_no,
            content=content,
            file_asset=file_asset,
        ),
        created_by=actor,
        updated_by=actor,
    )
    version.full_clean()
    version.save()
    record_event(
        actor=actor,
        object_type="documents.DocumentVersion",
        object_id=version.pk,
        action="document_version.created",
        result=EventResult.SUCCESS,
        context={"document_id": str(document.pk), "version_no": version_no},
    )
    return version


@transaction.atomic
def update_document_draft(
    *,
    actor: User,
    version: DocumentVersion,
    content: str = "",
    file_asset: FileAsset | None = None,
) -> DocumentVersion:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    locked = DocumentVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != VersionStatus.DRAFT:
        raise ValidationError("Solo una versión en borrador puede editarse.")
    locked.content = content
    locked.file_asset = file_asset
    locked.version_hash = document_version_hash(
        document=locked.document,
        version_no=locked.version_no,
        content=content,
        file_asset=file_asset,
    )
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=["content", "file_asset", "version_hash", "updated_by", "updated_at"]
    )
    record_event(
        actor=actor,
        object_type="documents.DocumentVersion",
        object_id=locked.pk,
        action="document_version.updated",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def submit_document_version(*, actor: User, version: DocumentVersion) -> DocumentVersion:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    locked = DocumentVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != VersionStatus.DRAFT:
        raise ValidationError("Solo un borrador puede enviarse a revisión.")
    locked.status = VersionStatus.IN_REVIEW
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
        object_type="documents.DocumentVersion",
        object_id=locked.pk,
        action="document_version.submitted",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def reject_document_version(
    *,
    actor: User,
    version: DocumentVersion,
    reason: str,
) -> DocumentVersion:
    _require(actor, Capability.REVIEW_DOCUMENTS)
    normalized_reason = _require_reason(reason)
    locked = DocumentVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != VersionStatus.IN_REVIEW:
        raise ValidationError("Solo una versión en revisión puede rechazarse.")
    locked.status = VersionStatus.DRAFT
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
        object_type="documents.DocumentVersion",
        object_id=locked.pk,
        action="document_version.rejected",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"version_no": locked.version_no},
    )
    return locked


def _supersede_effective_document_versions(
    *,
    actor: User,
    version: DocumentVersion,
    valid_from: date,
    valid_to: date | None,
) -> None:
    candidates = DocumentVersion.objects.select_for_update().filter(
        document=version.document,
        status__in=[VersionStatus.APPROVED, VersionStatus.EFFECTIVE],
    ).exclude(pk=version.pk)
    for other in candidates:
        if other.valid_from is None:
            raise ValidationError("La versión aprobada existente carece de inicio de vigencia.")
        if not date_ranges_overlap(other.valid_from, other.valid_to, valid_from, valid_to):
            continue
        if (
            other.status == VersionStatus.EFFECTIVE
            and other.valid_from is not None
            and other.valid_from < valid_from
        ):
            other.valid_to = valid_from - timedelta(days=1)
            if valid_from <= timezone.localdate():
                other.status = VersionStatus.SUPERSEDED
            other.updated_by = actor
            other.save(update_fields=["valid_to", "status", "updated_by", "updated_at"])
            continue
        raise ValidationError("La vigencia propuesta se superpone con otra versión aprobada.")


@transaction.atomic
def approve_document_version(
    *,
    actor: User,
    version: DocumentVersion,
    valid_from: date,
    valid_to: date | None = None,
    reason: str = "",
) -> DocumentVersion:
    _require(actor, Capability.APPROVE_DOCUMENTS)
    locked = DocumentVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != VersionStatus.IN_REVIEW:
        raise ValidationError("Solo una versión en revisión puede aprobarse.")
    if locked.created_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propia versión.")
    if valid_to is not None and valid_to < valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")
    _supersede_effective_document_versions(
        actor=actor,
        version=locked,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    locked.status = (
        VersionStatus.EFFECTIVE if valid_from <= timezone.localdate() else VersionStatus.APPROVED
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
        object_type="documents.DocumentVersion",
        object_id=locked.pk,
        action="document_version.approved",
        result=EventResult.SUCCESS,
        reason=locked.decision_reason,
        context={"status": locked.status, "version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def annul_document_version(
    *,
    actor: User,
    version: DocumentVersion,
    reason: str,
) -> DocumentVersion:
    _require(actor, Capability.APPROVE_DOCUMENTS)
    normalized_reason = _require_reason(reason)
    locked = DocumentVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status in {VersionStatus.SUPERSEDED, VersionStatus.ANNULLED}:
        raise ValidationError("La versión ya no admite anulación.")
    today = timezone.localdate()
    if locked.status == VersionStatus.EFFECTIVE and (
        locked.valid_to is None or locked.valid_to > today
    ):
        locked.valid_to = today
    locked.status = VersionStatus.ANNULLED
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
        object_type="documents.DocumentVersion",
        object_id=locked.pk,
        action="document_version.annulled",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def deactivate_document(*, actor: User, document: Document, reason: str) -> Document:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    normalized_reason = _require_reason(reason)
    locked = Document.objects.select_for_update().get(pk=document.pk)
    if not locked.is_active:
        raise ValidationError("El documento ya está inactivo.")
    open_statuses = [
        VersionStatus.DRAFT,
        VersionStatus.IN_REVIEW,
        VersionStatus.APPROVED,
        VersionStatus.EFFECTIVE,
    ]
    if locked.versions.filter(status__in=open_statuses).exists():
        raise ValidationError("Anule o sustituya las versiones abiertas antes de desactivar.")
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
        object_type="documents.Document",
        object_id=locked.pk,
        action="document.deactivated",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
    )
    return locked


@transaction.atomic
def create_reference_source(
    *,
    actor: User,
    code: str,
    issuer: str,
    title: str,
    reference_type: ReferenceType,
    source_url: str = "",
) -> ReferenceSource:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    _validate_no_compliance_claims(issuer, title)
    source = ReferenceSource(
        code=code,
        issuer=issuer,
        title=title,
        reference_type=reference_type,
        source_url=source_url,
        created_by=actor,
        updated_by=actor,
    )
    source.full_clean()
    source.save()
    record_event(
        actor=actor,
        object_type="documents.ReferenceSource",
        object_id=source.pk,
        action="reference_source.created",
        result=EventResult.SUCCESS,
        context={"code": source.code, "reference_type": source.reference_type},
    )
    return source


@transaction.atomic
def create_reference_version(
    *,
    actor: User,
    reference_source: ReferenceSource,
    consulted_at: datetime,
    summary: str,
    publication_date: date | None = None,
    content_hash: str | None = None,
) -> ReferenceVersion:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    locked_source = ReferenceSource.objects.select_for_update().get(pk=reference_source.pk)
    if not locked_source.is_active:
        raise ValidationError("La fuente de referencia debe estar activa.")
    _validate_no_compliance_claims(summary)
    last_version = locked_source.versions.aggregate(max_no=Max("version_no"))["max_no"] or 0
    version = ReferenceVersion(
        reference_source=locked_source,
        version_no=int(last_version) + 1,
        status=VersionStatus.DRAFT,
        publication_date=publication_date,
        consulted_at=consulted_at,
        summary=summary,
        content_hash=content_hash.casefold() if content_hash else None,
        created_by=actor,
        updated_by=actor,
    )
    version.full_clean()
    version.save()
    record_event(
        actor=actor,
        object_type="documents.ReferenceVersion",
        object_id=version.pk,
        action="reference_version.created",
        result=EventResult.SUCCESS,
        context={"source_id": str(reference_source.pk), "version_no": version.version_no},
    )
    return version


@transaction.atomic
def update_reference_draft(
    *,
    actor: User,
    version: ReferenceVersion,
    consulted_at: datetime,
    summary: str,
    publication_date: date | None = None,
    content_hash: str | None = None,
) -> ReferenceVersion:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    _validate_no_compliance_claims(summary)
    locked = ReferenceVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != VersionStatus.DRAFT:
        raise ValidationError("Solo una referencia en borrador puede editarse.")
    locked.consulted_at = consulted_at
    locked.summary = summary
    locked.publication_date = publication_date
    locked.content_hash = content_hash.casefold() if content_hash else None
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "consulted_at",
            "summary",
            "publication_date",
            "content_hash",
            "updated_by",
            "updated_at",
        ]
    )
    record_event(
        actor=actor,
        object_type="documents.ReferenceVersion",
        object_id=locked.pk,
        action="reference_version.updated",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def submit_reference_version(*, actor: User, version: ReferenceVersion) -> ReferenceVersion:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    locked = ReferenceVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != VersionStatus.DRAFT:
        raise ValidationError("Solo un borrador puede enviarse a revisión.")
    locked.status = VersionStatus.IN_REVIEW
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
        object_type="documents.ReferenceVersion",
        object_id=locked.pk,
        action="reference_version.submitted",
        result=EventResult.SUCCESS,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def reject_reference_version(
    *,
    actor: User,
    version: ReferenceVersion,
    reason: str,
) -> ReferenceVersion:
    _require(actor, Capability.REVIEW_DOCUMENTS)
    normalized_reason = _require_reason(reason)
    locked = ReferenceVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != VersionStatus.IN_REVIEW:
        raise ValidationError("Solo una referencia en revisión puede rechazarse.")
    locked.status = VersionStatus.DRAFT
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
        object_type="documents.ReferenceVersion",
        object_id=locked.pk,
        action="reference_version.rejected",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def approve_reference_version(
    *,
    actor: User,
    version: ReferenceVersion,
    valid_from: date,
    valid_to: date | None = None,
    reason: str = "",
) -> ReferenceVersion:
    _require(actor, Capability.APPROVE_DOCUMENTS)
    locked = ReferenceVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status != VersionStatus.IN_REVIEW:
        raise ValidationError("Solo una referencia en revisión puede aprobarse.")
    if locked.created_by_id == actor.pk:
        raise PermissionDenied("El autor no puede aprobar su propia referencia.")
    if valid_to is not None and valid_to < valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")
    candidates = ReferenceVersion.objects.select_for_update().filter(
        reference_source=locked.reference_source,
        status__in=[VersionStatus.APPROVED, VersionStatus.EFFECTIVE],
    ).exclude(pk=locked.pk)
    for other in candidates:
        if other.valid_from is None:
            raise ValidationError("La referencia aprobada carece de inicio de vigencia.")
        if not date_ranges_overlap(other.valid_from, other.valid_to, valid_from, valid_to):
            continue
        if (
            other.status == VersionStatus.EFFECTIVE
            and other.valid_from is not None
            and other.valid_from < valid_from
        ):
            other.valid_to = valid_from - timedelta(days=1)
            if valid_from <= timezone.localdate():
                other.status = VersionStatus.SUPERSEDED
            other.updated_by = actor
            other.save(update_fields=["valid_to", "status", "updated_by", "updated_at"])
            continue
        raise ValidationError("La vigencia se superpone con otra referencia aprobada.")
    locked.status = (
        VersionStatus.EFFECTIVE if valid_from <= timezone.localdate() else VersionStatus.APPROVED
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
        object_type="documents.ReferenceVersion",
        object_id=locked.pk,
        action="reference_version.approved",
        result=EventResult.SUCCESS,
        reason=locked.decision_reason,
        context={"status": locked.status, "version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def annul_reference_version(
    *,
    actor: User,
    version: ReferenceVersion,
    reason: str,
) -> ReferenceVersion:
    _require(actor, Capability.APPROVE_DOCUMENTS)
    normalized_reason = _require_reason(reason)
    locked = ReferenceVersion.objects.select_for_update().get(pk=version.pk)
    if locked.status in {VersionStatus.SUPERSEDED, VersionStatus.ANNULLED}:
        raise ValidationError("La referencia ya no admite anulación.")
    today = timezone.localdate()
    if locked.status == VersionStatus.EFFECTIVE and (
        locked.valid_to is None or locked.valid_to > today
    ):
        locked.valid_to = today
    locked.status = VersionStatus.ANNULLED
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
        object_type="documents.ReferenceVersion",
        object_id=locked.pk,
        action="reference_version.annulled",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
        context={"version_no": locked.version_no},
    )
    return locked


@transaction.atomic
def deactivate_reference_source(
    *,
    actor: User,
    reference_source: ReferenceSource,
    reason: str,
) -> ReferenceSource:
    _require(actor, Capability.MANAGE_DOCUMENTS)
    normalized_reason = _require_reason(reason)
    locked = ReferenceSource.objects.select_for_update().get(pk=reference_source.pk)
    if not locked.is_active:
        raise ValidationError("La fuente ya está inactiva.")
    open_statuses = [
        VersionStatus.DRAFT,
        VersionStatus.IN_REVIEW,
        VersionStatus.APPROVED,
        VersionStatus.EFFECTIVE,
    ]
    if locked.versions.filter(status__in=open_statuses).exists():
        raise ValidationError("Anule o sustituya las versiones antes de desactivar la fuente.")
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
        object_type="documents.ReferenceSource",
        object_id=locked.pk,
        action="reference_source.deactivated",
        result=EventResult.SUCCESS,
        reason=normalized_reason,
    )
    return locked
