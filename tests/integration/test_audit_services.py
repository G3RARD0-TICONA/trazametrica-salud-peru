from __future__ import annotations

import hashlib
from datetime import date, timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.auditlog.models import AuditEvent
from apps.audits.models import (
    AuditExecutionStatus,
    AuditPlan,
    AuditPlanStatus,
    AuditResponseResult,
    ChecklistResponseType,
    ChecklistVersionStatus,
    Finding,
    FindingImpact,
    FindingStatus,
    FindingType,
)
from apps.audits.services import (
    add_checklist_item,
    approve_audit_plan,
    approve_checklist_version,
    approve_execution,
    cancel_finding,
    create_audit_plan,
    create_checklist,
    create_checklist_version,
    create_finding,
    record_audit_response,
    reject_audit_plan,
    reject_execution,
    start_audit_execution,
    submit_audit_plan,
    submit_checklist_version,
    submit_execution_review,
    update_audit_plan,
)
from apps.documents.models import FileAsset, ScanStatus
from apps.organizations.models import Organization

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def role_user(*, admin_user: User, username: str, role_code: str) -> User:
    user = User.objects.create_user(
        username=username,
        password="Clave-Sintetica-2026",
        email=f"{username}@example.invalid",
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
    assign_role(
        actor=admin_user,
        user=user,
        role=role,
        valid_from=timezone.localdate(),
    )
    return user


def clean_evidence(*, admin_user: User, suffix: str = "001") -> FileAsset:
    digest = hashlib.sha256(f"evidencia-{suffix}".encode()).hexdigest()
    return FileAsset.objects.create(
        storage_key=f"documents/audits/evidencia-{suffix}.txt",
        original_name=f"evidencia-{suffix}.txt",
        media_type="text/plain",
        size_bytes=10,
        sha256=digest,
        scan_status=ScanStatus.CLEAN,
        synthetic_confirmed=True,
        created_by=admin_user,
        updated_by=admin_user,
    )


def approved_plan_and_checklist(
    *, admin_user: User, organization: Organization
) -> tuple[User, User, User, AuditPlan, object, list[object]]:
    planner = role_user(
        admin_user=admin_user, username="calidad_p12", role_code="QUALITY_MANAGER"
    )
    auditor = role_user(
        admin_user=admin_user, username="auditor_p12", role_code="AUDITOR"
    )
    approver = role_user(
        admin_user=admin_user, username="aprobador_p12", role_code="APPROVER"
    )
    plan = create_audit_plan(
        actor=planner,
        organization=organization,
        code=" aud-001 ",
        scope="Proceso administrativo sintético",
        criteria="Criterio interno de prueba",
        lead_auditor=auditor,
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate() + timedelta(days=2),
    )
    submit_audit_plan(actor=planner, plan=plan)
    plan = approve_audit_plan(
        actor=approver, plan=plan, reason="Plan sintético conforme"
    )
    checklist = create_checklist(
        actor=planner,
        organization=organization,
        code="lst-001",
        name="Lista de prueba",
    )
    version = create_checklist_version(actor=planner, checklist=checklist)
    first = add_checklist_item(
        actor=planner,
        version=version,
        criterion="Existe control administrativo sintético.",
        response_type=ChecklistResponseType.COMPLIANCE,
    )
    second = add_checklist_item(
        actor=planner,
        version=version,
        criterion="La evidencia sintética es trazable.",
        response_type=ChecklistResponseType.COMPLIANCE,
    )
    submit_checklist_version(actor=planner, version=version)
    version = approve_checklist_version(
        actor=approver,
        version=version,
        valid_from=timezone.localdate(),
        reason="Lista sintética conforme",
    )
    return planner, auditor, approver, plan, version, [first, second]


def test_plan_checklist_execution_finding_and_independent_completion(
    admin_user: User, organization: Organization
) -> None:
    planner, auditor, approver, plan, version, items = approved_plan_and_checklist(
        admin_user=admin_user, organization=organization
    )
    assert plan.code == "AUD-001"
    assert plan.status == AuditPlanStatus.APPROVED
    assert version.status == ChecklistVersionStatus.EFFECTIVE
    execution = start_audit_execution(
        actor=auditor, plan=plan, checklist_version=version
    )
    first_response = record_audit_response(
        actor=auditor,
        execution=execution,
        checklist_item=items[0],
        result=AuditResponseResult.CONFORM,
    )
    second_response = record_audit_response(
        actor=auditor,
        execution=execution,
        checklist_item=items[1],
        result=AuditResponseResult.NONCONFORM,
        observation="Falta evidencia administrativa sintética.",
    )
    assert first_response.observation == ""
    with pytest.raises(ValidationError, match="evidencia"):
        create_finding(
            actor=auditor,
            execution=execution,
            audit_response=second_response,
            code="HAL-001",
            finding_type=FindingType.NONCONFORMITY,
            criterion=items[1].criterion,
            condition="Condición sintética",
            impact=FindingImpact.HIGH,
            owner=planner,
            due_date=timezone.localdate() + timedelta(days=15),
        )
    asset = clean_evidence(admin_user=admin_user)
    finding = create_finding(
        actor=auditor,
        execution=execution,
        audit_response=second_response,
        code="HAL-001",
        finding_type=FindingType.NONCONFORMITY,
        criterion=items[1].criterion,
        condition="No se encontró evidencia administrativa sintética.",
        impact=FindingImpact.HIGH,
        owner=planner,
        due_date=timezone.localdate() + timedelta(days=15),
        evidence=[(asset, "Archivo textual sintético")],
    )
    assert finding.evidence.count() == 1
    submitted = submit_execution_review(actor=auditor, execution=execution)
    assert submitted.status == AuditExecutionStatus.IN_REVIEW
    with pytest.raises(PermissionDenied):
        approve_execution(
            actor=auditor, execution=submitted, reason="Autoaprobación indebida"
        )
    completed = approve_execution(
        actor=approver, execution=submitted, reason="Ejecución revisada"
    )
    plan.refresh_from_db()
    assert completed.status == AuditExecutionStatus.COMPLETED
    assert completed.completed_at is not None
    assert plan.status == AuditPlanStatus.COMPLETED
    assert AuditEvent.objects.filter(action="audit_execution.completed").exists()


def test_rejection_paths_required_responses_and_nonconformity_trace(
    admin_user: User, organization: Organization
) -> None:
    planner, auditor, approver, plan, version, items = approved_plan_and_checklist(
        admin_user=admin_user, organization=organization
    )
    execution = start_audit_execution(
        actor=auditor, plan=plan, checklist_version=version
    )
    response = record_audit_response(
        actor=auditor,
        execution=execution,
        checklist_item=items[0],
        result=AuditResponseResult.NONCONFORM,
        observation="Desviación sintética",
    )
    with pytest.raises(ValidationError, match="obligatorios"):
        submit_execution_review(actor=auditor, execution=execution)
    record_audit_response(
        actor=auditor,
        execution=execution,
        checklist_item=items[1],
        result=AuditResponseResult.CONFORM,
    )
    with pytest.raises(ValidationError, match="hallazgo"):
        submit_execution_review(actor=auditor, execution=execution)
    create_finding(
        actor=auditor,
        execution=execution,
        audit_response=response,
        code="HAL-RECH",
        finding_type=FindingType.NONCONFORMITY,
        criterion=response.checklist_item.criterion,
        condition="Desviación sintética trazada",
        impact=FindingImpact.MEDIUM,
        owner=planner,
        due_date=timezone.localdate() + timedelta(days=10),
        evidence_absence_reason="Archivo no requerido para esta prueba sintética.",
    )
    submitted = submit_execution_review(actor=auditor, execution=execution)
    rejected = reject_execution(
        actor=planner, execution=submitted, reason="Completar observación sintética"
    )
    assert rejected.status == AuditExecutionStatus.IN_PROGRESS
    assert rejected.decision_reason
    with pytest.raises(ValidationError, match="motivo"):
        reject_execution(actor=planner, execution=submitted, reason=" ")
    assert approver.is_active


def test_plan_rejection_editing_and_self_approval_are_controlled(
    admin_user: User, organization: Organization
) -> None:
    planner = role_user(
        admin_user=admin_user, username="calidad_rechazo", role_code="QUALITY_MANAGER"
    )
    approver = role_user(
        admin_user=admin_user, username="aprobador_rechazo", role_code="APPROVER"
    )
    plan = create_audit_plan(
        actor=planner,
        organization=organization,
        code="AUD-RECH",
        scope="Alcance inicial",
        criteria="Criterio inicial",
        lead_auditor=planner,
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate() + timedelta(days=1),
    )
    plan = update_audit_plan(
        actor=planner,
        plan=plan,
        scope="Alcance corregido",
        criteria="Criterio corregido",
        lead_auditor=planner,
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate() + timedelta(days=2),
    )
    submit_audit_plan(actor=planner, plan=plan)
    rejected = reject_audit_plan(
        actor=approver, plan=plan, reason="Ajustar alcance sintético"
    )
    assert rejected.status == AuditPlanStatus.DRAFT
    self_plan = create_audit_plan(
        actor=admin_user,
        organization=organization,
        code="AUD-SELF",
        scope="Alcance sintético",
        criteria="Criterio sintético",
        lead_auditor=admin_user,
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate(),
    )
    submit_audit_plan(actor=admin_user, plan=self_plan)
    with pytest.raises(PermissionDenied, match="propio"):
        approve_audit_plan(
            actor=admin_user, plan=self_plan, reason="No debe autoaprobarse"
        )


def test_finding_cancellation_permissions_and_protected_history(
    admin_user: User, organization: Organization, regular_user: User
) -> None:
    planner, auditor, _approver, plan, version, items = approved_plan_and_checklist(
        admin_user=admin_user, organization=organization
    )
    execution = start_audit_execution(
        actor=auditor, plan=plan, checklist_version=version
    )
    response = record_audit_response(
        actor=auditor,
        execution=execution,
        checklist_item=items[0],
        result=AuditResponseResult.OBSERVATION,
        observation="Observación sintética",
    )
    finding = create_finding(
        actor=auditor,
        execution=execution,
        audit_response=response,
        code="HAL-CAN",
        finding_type=FindingType.OBSERVATION,
        criterion=items[0].criterion,
        condition="Condición sintética",
        impact=FindingImpact.LOW,
        owner=planner,
        due_date=timezone.localdate() + timedelta(days=20),
        evidence_absence_reason="Justificación sintética documentada.",
    )
    with pytest.raises(PermissionDenied):
        cancel_finding(actor=regular_user, finding=finding, reason="Sin permiso")
    cancelled = cancel_finding(
        actor=planner, finding=finding, reason="Registro duplicado sintético"
    )
    assert cancelled.status == FindingStatus.CANCELLED
    with pytest.raises(ValidationError):
        Finding.objects.filter(pk=cancelled.pk).update(status=FindingStatus.OPEN)
    with pytest.raises(ValidationError):
        cancelled.delete()


def test_database_constraints_reject_invalid_dates(
    admin_user: User, organization: Organization
) -> None:
    with pytest.raises(ValidationError):
        create_audit_plan(
            actor=admin_user,
            organization=organization,
            code="AUD-DATE",
            scope="Alcance sintético",
            criteria="Criterio sintético",
            lead_auditor=admin_user,
            planned_start=date(2026, 2, 2),
            planned_end=date(2026, 2, 1),
        )
