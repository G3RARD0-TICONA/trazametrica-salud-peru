from __future__ import annotations

import hashlib
from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role, deactivate_user
from apps.auditlog.models import AuditEvent
from apps.audits.models import (
    ChecklistResponseType,
    Finding,
    FindingImpact,
    FindingStatus,
    FindingType,
)
from apps.audits.services import (
    add_checklist_item,
    approve_audit_plan,
    approve_checklist_version,
    create_audit_plan,
    create_checklist,
    create_checklist_version,
    create_finding,
    start_audit_execution,
    submit_audit_plan,
    submit_checklist_version,
)
from apps.documents.models import FileAsset, ScanStatus
from apps.improvements.models import (
    CorrectiveAction,
    CorrectiveActionStatus,
    EffectivenessResult,
    RootCauseMethod,
    RootCauseStatus,
)
from apps.improvements.selectors import corrective_action_alert_status
from apps.improvements.services import (
    add_action_evidence,
    approve_corrective_action,
    approve_root_cause_analysis,
    create_corrective_action,
    create_root_cause_analysis,
    reassign_corrective_action,
    restart_reopened_action,
    review_action_effectiveness,
    submit_action_verification,
    submit_corrective_action,
    submit_root_cause_analysis,
)
from apps.organizations.models import Organization

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def role_user(
    *, admin_user: User, username: str, role_code: str, active: bool = True
) -> User:
    user = User.objects.create_user(
        username=username,
        password="Clave-Sintetica-2026",
        email=f"{username}@example.invalid",
        is_active=active,
        created_by=admin_user,
        updated_by=admin_user,
    )
    role, _ = Role.objects.get_or_create(
        code=role_code,
        defaults={
            "name": role_code.replace("_", " ").title(),
            "is_approval_role": role_code == "APPROVER",
            "created_by": admin_user,
            "updated_by": admin_user,
        },
    )
    if active:
        assign_role(
            actor=admin_user,
            user=user,
            role=role,
            valid_from=timezone.localdate(),
        )
    return user


def add_role(*, admin_user: User, user: User, role_code: str) -> None:
    role, _ = Role.objects.get_or_create(
        code=role_code,
        defaults={
            "name": role_code.replace("_", " ").title(),
            "is_approval_role": role_code == "APPROVER",
            "created_by": admin_user,
            "updated_by": admin_user,
        },
    )
    assign_role(
        actor=admin_user,
        user=user,
        role=role,
        valid_from=timezone.localdate(),
    )


def clean_evidence(*, admin_user: User, suffix: str) -> FileAsset:
    digest = hashlib.sha256(f"p13-evidencia-{suffix}".encode()).hexdigest()
    return FileAsset.objects.create(
        storage_key=f"documents/improvements/evidencia-{suffix}.txt",
        original_name=f"evidencia-{suffix}.txt",
        media_type="text/plain",
        size_bytes=20,
        sha256=digest,
        scan_status=ScanStatus.CLEAN,
        synthetic_confirmed=True,
        created_by=admin_user,
        updated_by=admin_user,
    )


def build_finding(
    *, admin_user: User, organization: Organization, suffix: str
) -> tuple[User, User, User, Finding]:
    manager = role_user(
        admin_user=admin_user,
        username=f"calidad_{suffix}",
        role_code="QUALITY_MANAGER",
    )
    auditor = role_user(
        admin_user=admin_user,
        username=f"auditor_{suffix}",
        role_code="AUDITOR",
    )
    owner = role_user(
        admin_user=admin_user,
        username=f"owner_{suffix}",
        role_code="PROCESS_OWNER",
    )
    approver = role_user(
        admin_user=admin_user,
        username=f"approver_{suffix}",
        role_code="APPROVER",
    )
    plan = create_audit_plan(
        actor=manager,
        organization=organization,
        code=f"AUD-{suffix}",
        scope="Proceso administrativo sintético",
        criteria="Criterio interno sintético",
        lead_auditor=auditor,
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate() + timedelta(days=1),
    )
    submit_audit_plan(actor=manager, plan=plan)
    plan = approve_audit_plan(actor=approver, plan=plan, reason="Plan conforme")
    checklist = create_checklist(
        actor=manager,
        organization=organization,
        code=f"LST-{suffix}",
        name="Lista sintética",
    )
    version = create_checklist_version(actor=manager, checklist=checklist)
    add_checklist_item(
        actor=manager,
        version=version,
        criterion="Existe control administrativo sintético.",
        response_type=ChecklistResponseType.COMPLIANCE,
    )
    submit_checklist_version(actor=manager, version=version)
    version = approve_checklist_version(
        actor=approver,
        version=version,
        valid_from=timezone.localdate(),
        reason="Lista conforme",
    )
    execution = start_audit_execution(
        actor=auditor, plan=plan, checklist_version=version
    )
    finding = create_finding(
        actor=auditor,
        execution=execution,
        code=f"HAL-{suffix}",
        finding_type=FindingType.NONCONFORMITY,
        criterion="Criterio administrativo sintético",
        condition="Condición sintética sin control suficiente",
        impact=FindingImpact.HIGH,
        owner=manager,
        due_date=timezone.localdate() + timedelta(days=20),
        evidence_absence_reason="Justificación exclusivamente sintética.",
    )
    return manager, owner, approver, finding


def approved_root_cause(
    *, manager: User, approver: User, finding: Finding
):
    root_cause = create_root_cause_analysis(
        actor=manager,
        finding=finding,
        method=RootCauseMethod.FIVE_WHYS,
        analysis="Por qué 1 a 5 documentados con información sintética.",
        conclusion="Causa administrativa sintética controlable.",
    )
    submit_root_cause_analysis(actor=manager, root_cause=root_cause)
    return approve_root_cause_analysis(
        actor=approver, root_cause=root_cause, reason="Causa trazable"
    )


def approved_action(
    *, manager: User, owner: User, approver: User, root_cause, code: str
) -> CorrectiveAction:
    action = create_corrective_action(
        actor=manager,
        root_cause=root_cause,
        code=code,
        description="Implementar control administrativo sintético.",
        owner=owner,
        due_date=timezone.localdate() + timedelta(days=10),
        effectiveness_criterion="Control aplicado y sin recurrencia sintética.",
    )
    submit_corrective_action(actor=manager, action=action)
    return approve_corrective_action(
        actor=approver, action=action, reason="Acción viable"
    )


def test_cause_action_evidence_independent_effectiveness_and_closure(
    admin_user: User, organization: Organization
) -> None:
    manager, owner, approver, finding = build_finding(
        admin_user=admin_user, organization=organization, suffix="P13A"
    )
    root_cause = create_root_cause_analysis(
        actor=manager,
        finding=finding,
        method=RootCauseMethod.ISHIKAWA,
        analysis="Personas, método, medición y entorno sintéticos.",
        conclusion="Control administrativo no estandarizado.",
    )
    submit_root_cause_analysis(actor=manager, root_cause=root_cause)
    add_role(admin_user=admin_user, user=manager, role_code="APPROVER")
    with pytest.raises(PermissionDenied, match="propio"):
        approve_root_cause_analysis(
            actor=manager, root_cause=root_cause, reason="Autoaprobación indebida"
        )
    root_cause = approve_root_cause_analysis(
        actor=approver, root_cause=root_cause, reason="Causa sustentada"
    )
    assert root_cause.status == RootCauseStatus.APPROVED
    action = approved_action(
        manager=manager,
        owner=owner,
        approver=approver,
        root_cause=root_cause,
        code="ACP-001",
    )
    asset = clean_evidence(admin_user=admin_user, suffix="p13a")
    add_action_evidence(
        actor=owner, action=action, file_asset=asset, description="Control sintético aplicado"
    )
    action = submit_action_verification(actor=owner, action=action)
    add_role(admin_user=admin_user, user=owner, role_code="APPROVER")
    with pytest.raises(PermissionDenied, match="RN-018"):
        review_action_effectiveness(
            actor=owner,
            action=action,
            result=EffectivenessResult.EFFECTIVE,
            notes="Revisión propia indebida",
        )
    review = review_action_effectiveness(
        actor=approver,
        action=action,
        result=EffectivenessResult.EFFECTIVE,
        notes="Criterio sintético cumplido sin recurrencia ficticia.",
    )
    action.refresh_from_db()
    finding.refresh_from_db()
    assert review.reopens_action is False
    assert action.status == CorrectiveActionStatus.CLOSED
    assert finding.status == FindingStatus.CLOSED
    assert AuditEvent.objects.filter(
        action="corrective_action.effectiveness_reviewed"
    ).exists()
    with pytest.raises(ValidationError):
        action.delete()


def test_ineffective_review_reopens_action_and_finding(
    admin_user: User, organization: Organization
) -> None:
    manager, owner, approver, finding = build_finding(
        admin_user=admin_user, organization=organization, suffix="P13B"
    )
    root_cause = approved_root_cause(
        manager=manager, approver=approver, finding=finding
    )
    action = approved_action(
        manager=manager,
        owner=owner,
        approver=approver,
        root_cause=root_cause,
        code="ACP-002",
    )
    add_action_evidence(
        actor=owner,
        action=action,
        file_asset=clean_evidence(admin_user=admin_user, suffix="p13b"),
        description="Evidencia sintética insuficiente para eficacia",
    )
    action = submit_action_verification(actor=owner, action=action)
    review = review_action_effectiveness(
        actor=approver,
        action=action,
        result=EffectivenessResult.INEFFECTIVE,
        notes="El criterio sintético no se sostuvo.",
    )
    action.refresh_from_db()
    finding.refresh_from_db()
    assert review.reopens_action is True
    assert action.status == CorrectiveActionStatus.REOPENED
    assert finding.status == FindingStatus.REOPENED
    restarted = restart_reopened_action(
        actor=owner, action=action, reason="Reejecución sintética autorizada"
    )
    assert restarted.status == CorrectiveActionStatus.IN_PROGRESS
    assert restarted.completed_at is None


def test_rn015_rn017_rn019_and_atomic_evidence_rejection(
    admin_user: User, organization: Organization
) -> None:
    manager, owner, approver, finding = build_finding(
        admin_user=admin_user, organization=organization, suffix="P13C"
    )
    cause = create_root_cause_analysis(
        actor=manager,
        finding=finding,
        method=RootCauseMethod.PARETO,
        analysis="Frecuencias sintéticas ordenadas.",
        conclusion="Causa prioritaria sintética.",
    )
    with pytest.raises(ValidationError, match="RN-015"):
        create_corrective_action(
            actor=manager,
            root_cause=cause,
            code="ACP-BLOQ",
            description="No debe persistir",
            owner=owner,
            due_date=timezone.localdate() + timedelta(days=5),
            effectiveness_criterion="Criterio sintético",
        )
    assert CorrectiveAction.objects.count() == 0
    submit_root_cause_analysis(actor=manager, root_cause=cause)
    cause = approve_root_cause_analysis(
        actor=approver, root_cause=cause, reason="Causa aprobada"
    )
    first = approved_action(
        manager=manager,
        owner=owner,
        approver=approver,
        root_cause=cause,
        code="ACP-003",
    )
    second = approved_action(
        manager=manager,
        owner=owner,
        approver=approver,
        root_cause=cause,
        code="ACP-004",
    )
    dirty = clean_evidence(admin_user=admin_user, suffix="dirty")
    dirty.scan_status = ScanStatus.REJECTED
    dirty.save(update_fields=["scan_status"])
    with pytest.raises(ValidationError, match="validada"):
        add_action_evidence(
            actor=owner,
            action=first,
            file_asset=dirty,
            description="Debe rechazarse",
        )
    assert first.evidence.count() == 0
    add_action_evidence(
        actor=owner,
        action=first,
        file_asset=clean_evidence(admin_user=admin_user, suffix="p13c"),
        description="Evidencia sintética válida",
    )
    first = submit_action_verification(actor=owner, action=first)
    review_action_effectiveness(
        actor=approver,
        action=first,
        result=EffectivenessResult.EFFECTIVE,
        notes="Primera acción eficaz.",
    )
    finding.refresh_from_db()
    assert finding.status != FindingStatus.CLOSED
    deactivate_user(
        actor=admin_user, user=owner, reason="Inactividad sintética para probar RN-017"
    )
    second.refresh_from_db()
    assert corrective_action_alert_status(action=second) == "unassigned"
    replacement = role_user(
        admin_user=admin_user,
        username="owner_p13c_reemplazo",
        role_code="PROCESS_OWNER",
    )
    second = reassign_corrective_action(
        actor=manager,
        action=second,
        new_owner=replacement,
        reason="Responsable anterior inactivo",
    )
    assert second.owner == replacement
    assert AuditEvent.objects.filter(action="corrective_action.reassigned").exists()
