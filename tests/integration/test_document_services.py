from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.auditlog.models import AuditEvent
from apps.documents.models import (
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
from apps.documents.services import (
    annul_document_version,
    annul_reference_version,
    approve_document_version,
    approve_reference_version,
    create_document,
    create_document_version,
    create_reference_source,
    create_reference_version,
    deactivate_document,
    deactivate_reference_source,
    register_file_asset,
    reject_document_version,
    reject_reference_version,
    submit_document_version,
    submit_reference_version,
    update_document_draft,
    update_document_metadata,
    update_reference_draft,
)
from apps.organizations.models import Area, Organization

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def create_approver(*, admin_user: User) -> User:
    approver = User.objects.create_user(
        username="aprobador_sintetico",
        password="Clave-Sintetica-2026",
        created_by=admin_user,
        updated_by=admin_user,
    )
    role = Role.objects.create(
        code="APPROVER",
        name="Aprobación documental",
        is_approval_role=True,
        created_by=admin_user,
        updated_by=admin_user,
    )
    assign_role(
        actor=admin_user,
        user=approver,
        role=role,
        valid_from=timezone.localdate(),
    )
    return approver


def create_test_document(
    *,
    admin_user: User,
    organization: Organization,
    area: Area,
) -> Document:
    return create_document(
        actor=admin_user,
        organization=organization,
        responsible_area=area,
        code="  pro-001 ",
        title="Procedimiento sintético de calidad",
        document_type=DocumentType.PROCEDURE,
    )


def test_document_code_is_normalized_and_unique_in_organization(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    first = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    assert first.code == "PRO-001"
    with pytest.raises(ValidationError):
        create_document(
            actor=admin_user,
            organization=organization,
            responsible_area=area,
            code="PRO-001",
            title="Duplicado sintético",
            document_type=DocumentType.PROCEDURE,
        )


def test_document_requires_an_area_from_its_organization(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    other_organization = Organization(
        code="ORG-OTRA",
        name="Organización Sintética Inactiva",
        is_active=False,
        deactivated_at=timezone.now(),
        deactivated_by=admin_user,
        deactivation_reason="Solo para comprobar ámbito",
        created_by=admin_user,
        updated_by=admin_user,
    )
    other_organization.full_clean()
    other_organization.save()
    other_area = Area.objects.create(
        organization=other_organization,
        code="AREA-OTRA",
        name="Área Sintética Externa",
        created_by=admin_user,
        updated_by=admin_user,
    )
    with pytest.raises(ValidationError, match="pertenecer"):
        create_document(
            actor=admin_user,
            organization=organization,
            responsible_area=other_area,
            code="PRO-002",
            title="Documento sintético",
            document_type=DocumentType.PROCEDURE,
        )
    assert area.organization == organization


def test_file_asset_enforces_synthetic_safe_metadata(admin_user: User) -> None:
    asset = register_file_asset(
        actor=admin_user,
        storage_key="documents/2026/opaque-123",
        original_name="evidencia-sintetica.pdf",
        media_type="application/pdf",
        size_bytes=512,
        sha256="a" * 64,
        scan_status=ScanStatus.CLEAN,
        synthetic_confirmed=True,
    )
    assert asset.sha256 == "a" * 64
    with pytest.raises(ValidationError):
        register_file_asset(
            actor=admin_user,
            storage_key="../archivo-real",
            original_name="paciente.exe",
            media_type="application/octet-stream",
            size_bytes=512,
            sha256="x",
            scan_status=ScanStatus.CLEAN,
            synthetic_confirmed=False,
        )


def test_document_version_requires_exactly_one_clean_payload(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    with pytest.raises(ValidationError, match="texto o un archivo"):
        create_document_version(actor=admin_user, document=document)
    pending = register_file_asset(
        actor=admin_user,
        storage_key="documents/2026/opaque-pending",
        original_name="pendiente.pdf",
        media_type="application/pdf",
        size_bytes=512,
        sha256="b" * 64,
        scan_status=ScanStatus.PENDING,
        synthetic_confirmed=True,
    )
    with pytest.raises(ValidationError, match="escaneo limpio"):
        create_document_version(actor=admin_user, document=document, file_asset=pending)


def test_version_hash_and_number_are_deterministic(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    first = create_document_version(
        actor=admin_user,
        document=document,
        content="Contenido sintético v1",
    )
    second = create_document_version(
        actor=admin_user,
        document=document,
        content="Contenido sintético v2",
    )
    assert (first.version_no, second.version_no) == (1, 2)
    assert len(first.version_hash) == 64
    assert first.version_hash != second.version_hash


def test_draft_can_be_updated_rejected_and_resubmitted(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    updated_document = update_document_metadata(
        actor=admin_user,
        document=document,
        title="Procedimiento sintético actualizado",
        responsible_area=area,
    )
    version = create_document_version(
        actor=admin_user,
        document=updated_document,
        content="Borrador inicial",
    )
    updated = update_document_draft(
        actor=admin_user,
        version=version,
        content="Borrador corregido",
    )
    assert updated.content == "Borrador corregido"
    submit_document_version(actor=admin_user, version=updated)
    rejected = reject_document_version(
        actor=admin_user,
        version=updated,
        reason="Requiere precisión sintética",
    )
    assert rejected.status == VersionStatus.DRAFT
    assert rejected.reviewed_by == admin_user
    assert rejected.decision_reason == "Requiere precisión sintética"


def test_document_with_open_draft_cannot_be_deactivated(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    create_document_version(actor=admin_user, document=document, content="Borrador abierto")
    with pytest.raises(ValidationError, match="versiones abiertas"):
        deactivate_document(actor=admin_user, document=document, reason="Intento sintético")


def test_author_cannot_approve_own_version(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    version = create_document_version(
        actor=admin_user,
        document=document,
        content="Contenido sintético",
    )
    submit_document_version(actor=admin_user, version=version)
    with pytest.raises(PermissionDenied, match="propia versión"):
        approve_document_version(
            actor=admin_user,
            version=version,
            valid_from=timezone.localdate(),
        )


def test_approval_makes_content_immutable_and_is_audited(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    approver = create_approver(admin_user=admin_user)
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    version = create_document_version(
        actor=admin_user,
        document=document,
        content="Contenido sintético aprobado",
    )
    submit_document_version(actor=admin_user, version=version)
    approved = approve_document_version(
        actor=approver,
        version=version,
        valid_from=timezone.localdate(),
        reason="Revisión sintética conforme",
    )
    assert approved.status == VersionStatus.EFFECTIVE
    assert approved.approved_by == approver
    approved.content = "Intento de cambio"
    with pytest.raises(ValidationError, match="no permite cambiar"):
        approved.save()
    assert AuditEvent.objects.filter(
        object_id=approved.pk,
        action="document_version.approved",
    ).exists()


def test_new_effective_version_supersedes_previous_one(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    approver = create_approver(admin_user=admin_user)
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    today = timezone.localdate()
    first = create_document_version(actor=admin_user, document=document, content="Versión uno")
    submit_document_version(actor=admin_user, version=first)
    approve_document_version(actor=approver, version=first, valid_from=today)
    second = create_document_version(actor=admin_user, document=document, content="Versión dos")
    submit_document_version(actor=admin_user, version=second)
    approve_document_version(
        actor=approver,
        version=second,
        valid_from=today + timedelta(days=1),
    )
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.status == VersionStatus.EFFECTIVE
    assert first.valid_to == today
    assert second.status == VersionStatus.APPROVED


def test_annulment_requires_reason_and_allows_document_deactivation(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    approver = create_approver(admin_user=admin_user)
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    version = create_document_version(actor=admin_user, document=document, content="Versión")
    submit_document_version(actor=admin_user, version=version)
    approve_document_version(
        actor=approver,
        version=version,
        valid_from=timezone.localdate(),
    )
    with pytest.raises(ValidationError, match="motivo"):
        annul_document_version(actor=approver, version=version, reason="  ")
    annul_document_version(actor=approver, version=version, reason="Retiro sintético")
    inactive = deactivate_document(
        actor=admin_user,
        document=document,
        reason="Catálogo sustituido",
    )
    assert not inactive.is_active


def test_non_privileged_user_cannot_create_document(
    regular_user: User,
    organization: Organization,
    area: Area,
) -> None:
    with pytest.raises(PermissionDenied):
        create_document(
            actor=regular_user,
            organization=organization,
            responsible_area=area,
            code="PRO-DEN",
            title="Documento denegado",
            document_type=DocumentType.PROCEDURE,
        )


def test_reference_cannot_claim_certification(admin_user: User) -> None:
    with pytest.raises(ValidationError, match="certificación"):
        create_reference_source(
            actor=admin_user,
            code="REF-001",
            issuer="Entidad Sintética",
            title="Sistema certificado por una autoridad",
            reference_type=ReferenceType.STANDARD,
        )


def test_reference_version_uses_independent_approval(
    admin_user: User,
) -> None:
    approver = create_approver(admin_user=admin_user)
    source = create_reference_source(
        actor=admin_user,
        code="REF-001",
        issuer="Entidad Sintética",
        title="Guía demostrativa",
        reference_type=ReferenceType.GUIDELINE,
        source_url="https://example.invalid/guia",
    )
    version = create_reference_version(
        actor=admin_user,
        reference_source=source,
        consulted_at=timezone.now(),
        summary="Resumen exclusivamente sintético.",
        content_hash="c" * 64,
    )
    submit_reference_version(actor=admin_user, version=version)
    approved = approve_reference_version(
        actor=approver,
        version=version,
        valid_from=timezone.localdate(),
    )
    assert approved.status == VersionStatus.EFFECTIVE


def test_reference_draft_rejection_annulment_and_deactivation(
    admin_user: User,
) -> None:
    approver = create_approver(admin_user=admin_user)
    source = create_reference_source(
        actor=admin_user,
        code="REF-FLUJO",
        issuer="Entidad Sintética",
        title="Referencia de flujo",
        reference_type=ReferenceType.INTERNAL,
    )
    version = create_reference_version(
        actor=admin_user,
        reference_source=source,
        consulted_at=timezone.now(),
        summary="Resumen inicial sintético.",
    )
    version = update_reference_draft(
        actor=admin_user,
        version=version,
        consulted_at=timezone.now(),
        summary="Resumen corregido sintético.",
        publication_date=timezone.localdate(),
        content_hash="d" * 64,
    )
    submit_reference_version(actor=admin_user, version=version)
    rejected = reject_reference_version(
        actor=admin_user,
        version=version,
        reason="Revisión sintética pendiente",
    )
    assert rejected.status == VersionStatus.DRAFT
    submit_reference_version(actor=admin_user, version=rejected)
    approved = approve_reference_version(
        actor=approver,
        version=rejected,
        valid_from=timezone.localdate(),
    )
    annulled = annul_reference_version(
        actor=approver,
        version=approved,
        reason="Referencia sintética retirada",
    )
    assert annulled.status == VersionStatus.ANNULLED
    inactive = deactivate_reference_source(
        actor=admin_user,
        reference_source=source,
        reason="Catálogo sintético sustituido",
    )
    assert not inactive.is_active


def test_documental_records_and_audit_events_are_append_only(
    admin_user: User,
    organization: Organization,
    area: Area,
) -> None:
    document = create_test_document(
        admin_user=admin_user,
        organization=organization,
        area=area,
    )
    event = AuditEvent.objects.filter(object_id=document.pk).first()
    assert event is not None
    with pytest.raises(ValidationError, match="no se eliminan"):
        document.delete()
    with pytest.raises(ValidationError, match="inmutable"):
        event.delete()
    with pytest.raises(ValidationError, match="inmutable"):
        AuditEvent.objects.filter(pk=event.pk).update(reason="Mutación")


def test_expected_p08_tables_are_declared() -> None:
    assert FileAsset._meta.db_table == "documents_file_asset"
    assert Document._meta.db_table == "documents_document"
    assert DocumentVersion._meta.db_table == "documents_document_version"
    assert ReferenceSource._meta.db_table == "documents_reference_source"
    assert ReferenceVersion._meta.db_table == "documents_reference_version"
    assert AuditEvent._meta.db_table == "auditlog_event"
