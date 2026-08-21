from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.auditlog.models import AuditEvent
from apps.documents.models import DocumentType
from apps.documents.services import create_document
from apps.organizations.models import Area, Organization
from apps.processes.models import (
    Process,
    ProcessType,
    ProcessVersion,
    ProcessVersionStatus,
    SipocEntry,
    SipocEntryType,
)
from apps.processes.services import (
    add_sipoc_entry,
    annul_process_version,
    approve_process_version,
    create_process,
    create_process_version,
    deactivate_process,
    link_document_to_process,
    reject_process_version,
    remove_sipoc_entry,
    submit_process_version,
    update_process_draft,
    update_process_metadata,
    update_sipoc_entry,
)

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def create_approver(*, admin_user: User) -> User:
    approver = User.objects.create_user(
        username="aprobador_procesos",
        password="Clave-Sintetica-2026",
        created_by=admin_user,
        updated_by=admin_user,
    )
    role = Role.objects.create(
        code="APPROVER",
        name="Aprobación independiente",
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


def create_test_process(
    *, admin_user: User, organization: Organization, area: Area, code: str = " pro-001 "
) -> Process:
    return create_process(
        actor=admin_user,
        organization=organization,
        owner_area=area,
        code=code,
        name="Proceso sintético de calidad",
        process_type=ProcessType.OPERATIONAL,
    )


def complete_sipoc(*, admin_user: User, version: ProcessVersion) -> list[SipocEntry]:
    return [
        add_sipoc_entry(
            actor=admin_user,
            version=version,
            entry_type=entry_type,
            position=1,
            name=f"{entry_type.label} sintético",
            description="Descripción administrativa ficticia.",
        )
        for entry_type in SipocEntryType
    ]


def test_process_code_is_normalized_unique_and_metadata_is_editable(
    admin_user: User, organization: Organization, area: Area
) -> None:
    process = create_test_process(admin_user=admin_user, organization=organization, area=area)
    assert process.code == "PRO-001"
    updated = update_process_metadata(
        actor=admin_user,
        process=process,
        name="Proceso sintético actualizado",
        owner_area=area,
        process_type=ProcessType.SUPPORT,
    )
    assert updated.name == "Proceso sintético actualizado"
    assert updated.process_type == ProcessType.SUPPORT
    with pytest.raises(ValidationError):
        create_test_process(
            admin_user=admin_user, organization=organization, area=area, code="pro-001"
        )


def test_process_rejects_owner_area_from_another_organization(
    admin_user: User, organization: Organization, area: Area
) -> None:
    other = Organization.objects.create(
        code="ORG-OTRA",
        name="Organización sintética externa",
        is_active=False,
        deactivated_at=timezone.now(),
        deactivated_by=admin_user,
        deactivation_reason="Organización externa para prueba de ámbito",
        created_by=admin_user,
        updated_by=admin_user,
    )
    other_area = Area.objects.create(
        organization=other,
        code="AREA-OTRA",
        name="Área sintética externa",
        created_by=admin_user,
        updated_by=admin_user,
    )
    with pytest.raises(ValidationError, match="pertenecer"):
        create_test_process(
            admin_user=admin_user,
            organization=organization,
            area=other_area,
            code="PRO-OTRO",
        )
    assert area.organization == organization


def test_draft_requires_complete_sipoc_and_recalculates_hash(
    admin_user: User, organization: Organization, area: Area
) -> None:
    process = create_test_process(admin_user=admin_user, organization=organization, area=area)
    version = create_process_version(
        actor=admin_user,
        process=process,
        objective="Objetivo sintético",
        scope="Alcance sintético",
    )
    initial_hash = version.version_hash
    supplier = add_sipoc_entry(
        actor=admin_user,
        version=version,
        entry_type=SipocEntryType.SUPPLIER,
        position=1,
        name="Proveedor sintético",
    )
    version.refresh_from_db()
    assert version.version_hash != initial_hash
    supplier = update_sipoc_entry(
        actor=admin_user,
        entry=supplier,
        position=2,
        name="Proveedor sintético actualizado",
    )
    assert supplier.position == 2
    with pytest.raises(ValidationError, match="incompleto"):
        submit_process_version(actor=admin_user, version=version)
    remove_sipoc_entry(actor=admin_user, entry=supplier, reason="Corrección de prueba")
    assert not SipocEntry.objects.filter(pk=supplier.pk).exists()


def test_version_workflow_rejects_self_approval_and_preserves_approved_ficha(
    admin_user: User, organization: Organization, area: Area
) -> None:
    process = create_test_process(admin_user=admin_user, organization=organization, area=area)
    version = create_process_version(
        actor=admin_user,
        process=process,
        objective="Objetivo sintético",
        scope="Alcance sintético",
    )
    entries = complete_sipoc(admin_user=admin_user, version=version)
    submitted = submit_process_version(actor=admin_user, version=version)
    assert submitted.status == ProcessVersionStatus.IN_REVIEW
    with pytest.raises(PermissionDenied, match="propia versión"):
        approve_process_version(
            actor=admin_user,
            version=submitted,
            valid_from=timezone.localdate(),
        )
    approver = create_approver(admin_user=admin_user)
    approved = approve_process_version(
        actor=approver,
        version=submitted,
        valid_from=timezone.localdate(),
        reason="Ficha sintética conforme",
    )
    assert approved.status == ProcessVersionStatus.EFFECTIVE
    assert approved.approved_by == approver
    with pytest.raises(ValidationError, match="borrador"):
        update_process_draft(
            actor=admin_user,
            version=approved,
            objective="Cambio indebido",
            scope=approved.scope,
        )
    with pytest.raises(ValidationError, match="inmutable"):
        update_sipoc_entry(actor=admin_user, entry=entries[0], position=1, name="Cambio")
    assert AuditEvent.objects.filter(action="process_version.approved").exists()


def test_rejection_and_annulment_require_reason(
    admin_user: User, organization: Organization, area: Area
) -> None:
    process = create_test_process(admin_user=admin_user, organization=organization, area=area)
    version = create_process_version(
        actor=admin_user, process=process, objective="Objetivo", scope="Alcance"
    )
    complete_sipoc(admin_user=admin_user, version=version)
    submit_process_version(actor=admin_user, version=version)
    with pytest.raises(ValidationError, match="motivo"):
        reject_process_version(actor=admin_user, version=version, reason=" ")
    rejected = reject_process_version(
        actor=admin_user, version=version, reason="Ajustar el alcance sintético"
    )
    assert rejected.status == ProcessVersionStatus.DRAFT
    submit_process_version(actor=admin_user, version=rejected)
    approver = create_approver(admin_user=admin_user)
    approved = approve_process_version(
        actor=approver, version=rejected, valid_from=timezone.localdate()
    )
    with pytest.raises(ValidationError, match="motivo"):
        annul_process_version(actor=approver, version=approved, reason="")
    annulled = annul_process_version(
        actor=approver, version=approved, reason="Cierre administrativo sintético"
    )
    assert annulled.status == ProcessVersionStatus.ANNULLED
    inactive = deactivate_process(
        actor=admin_user, process=process, reason="Proceso sintético retirado"
    )
    assert not inactive.is_active


def test_new_effective_version_supersedes_prior_version(
    admin_user: User, organization: Organization, area: Area
) -> None:
    process = create_test_process(admin_user=admin_user, organization=organization, area=area)
    approver = create_approver(admin_user=admin_user)
    first = create_process_version(
        actor=admin_user, process=process, objective="Objetivo v1", scope="Alcance v1"
    )
    complete_sipoc(admin_user=admin_user, version=first)
    submit_process_version(actor=admin_user, version=first)
    approve_process_version(
        actor=approver,
        version=first,
        valid_from=timezone.localdate() - timedelta(days=10),
    )
    second = create_process_version(
        actor=admin_user, process=process, objective="Objetivo v2", scope="Alcance v2"
    )
    complete_sipoc(admin_user=admin_user, version=second)
    submit_process_version(actor=admin_user, version=second)
    approve_process_version(actor=approver, version=second, valid_from=timezone.localdate())
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.status == ProcessVersionStatus.SUPERSEDED
    assert first.valid_to == timezone.localdate() - timedelta(days=1)
    assert second.status == ProcessVersionStatus.EFFECTIVE


def test_document_process_link_requires_both_capabilities_and_same_scope(
    admin_user: User,
    regular_user: User,
    organization: Organization,
    area: Area,
) -> None:
    process = create_test_process(admin_user=admin_user, organization=organization, area=area)
    document = create_document(
        actor=admin_user,
        organization=organization,
        responsible_area=area,
        code="DOC-PROC",
        title="Documento de proceso sintético",
        document_type=DocumentType.PROCEDURE,
    )
    with pytest.raises(PermissionDenied):
        link_document_to_process(actor=regular_user, document=document, process=process)
    linked = link_document_to_process(actor=admin_user, document=document, process=process)
    assert linked.process == process
    assert process.documents.get() == document
    unlinked = link_document_to_process(actor=admin_user, document=linked, process=None)
    assert unlinked.process is None


def test_process_and_version_cannot_be_physically_deleted(
    admin_user: User, organization: Organization, area: Area
) -> None:
    process = create_test_process(admin_user=admin_user, organization=organization, area=area)
    version = create_process_version(
        actor=admin_user, process=process, objective="Objetivo", scope="Alcance"
    )
    with pytest.raises(ValidationError, match="físicamente"):
        process.delete()
    with pytest.raises(ValidationError, match="físicamente"):
        version.delete()
