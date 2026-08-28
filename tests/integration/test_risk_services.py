from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.services import assign_role
from apps.auditlog.models import AuditEvent
from apps.organizations.models import Area, Organization
from apps.processes.models import Process, ProcessType
from apps.risks.models import (
    AssessmentStatus,
    ControlFrequency,
    ControlReviewResult,
    ControlType,
    ControlVersionStatus,
    ExpectedEffectiveness,
    RiskStatus,
)
from apps.risks.selectors import control_alert_status, risk_alert_status
from apps.risks.services import (
    accept_residual_risk,
    approve_control_version,
    approve_risk_assessment,
    close_risk,
    create_control,
    create_control_version,
    create_risk,
    create_risk_assessment,
    link_risk_control,
    reopen_risk,
    review_control,
    submit_control_version,
    submit_risk_assessment,
)

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


def process_for_risk(
    *, admin_user: User, organization: Organization, area: Area, suffix: str
) -> Process:
    return Process.objects.create(
        organization=organization,
        owner_area=area,
        code=f"SOP-{suffix}",
        name=f"Proceso sintético {suffix}",
        process_type=ProcessType.SUPPORT,
        created_by=admin_user,
        updated_by=admin_user,
    )


def risk_actors(admin_user: User, suffix: str) -> tuple[User, User, User, User]:
    manager = role_user(
        admin_user=admin_user,
        username=f"calidad_risk_{suffix}",
        role_code="QUALITY_MANAGER",
    )
    owner = role_user(
        admin_user=admin_user,
        username=f"owner_risk_{suffix}",
        role_code="PROCESS_OWNER",
    )
    reviewer = role_user(
        admin_user=admin_user,
        username=f"auditor_risk_{suffix}",
        role_code="AUDITOR",
    )
    approver = role_user(
        admin_user=admin_user,
        username=f"approver_risk_{suffix}",
        role_code="APPROVER",
    )
    return manager, owner, reviewer, approver


def test_risk_control_review_and_independent_closure(
    admin_user: User, organization: Organization, area: Area
) -> None:
    manager, owner, reviewer, approver = risk_actors(admin_user, "FLOW")
    process = process_for_risk(
        admin_user=admin_user, organization=organization, area=area, suffix="FLOW"
    )
    risk = create_risk(
        actor=manager,
        organization=organization,
        process=process,
        code="RSK-FLOW",
        cause="Falta de revisión administrativa sintética.",
        event="Incumplimiento ficticio del plazo.",
        consequence="Retraso administrativo demostrativo.",
        owner=owner,
    )
    assessment = create_risk_assessment(
        actor=manager,
        risk=risk,
        probability=5,
        impact=5,
        residual_probability=2,
        residual_impact=2,
        next_review_date=timezone.localdate() + timedelta(days=30),
    )
    submit_risk_assessment(actor=manager, assessment=assessment)
    add_role(admin_user=admin_user, user=manager, role_code="APPROVER")
    with pytest.raises(PermissionDenied, match="propia"):
        approve_risk_assessment(
            actor=manager, assessment=assessment, reason="Autoaprobación indebida"
        )
    assessment = approve_risk_assessment(
        actor=approver, assessment=assessment, reason="Evaluación trazable"
    )
    assert assessment.status == AssessmentStatus.APPROVED
    risk.refresh_from_db()
    assert risk.status == RiskStatus.CONTROLLED

    control = create_control(
        actor=manager,
        organization=organization,
        code="CTL-FLOW",
        name="Revisión mensual sintética",
        owner=owner,
    )
    version = create_control_version(
        actor=manager,
        control=control,
        description="Verificar mensualmente los registros ficticios.",
        control_type=ControlType.PREVENTIVE,
        frequency=ControlFrequency.MONTHLY,
    )
    submit_control_version(actor=manager, version=version)
    version = approve_control_version(
        actor=approver,
        version=version,
        valid_from=timezone.localdate() - timedelta(days=1),
        reason="Control suficiente",
    )
    assert version.status == ControlVersionStatus.EFFECTIVE
    with pytest.raises(ValidationError, match="antes de la versión"):
        link_risk_control(
            actor=manager,
            risk=risk,
            control_version=version,
            valid_from=timezone.localdate() - timedelta(days=2),
            effectiveness_expected=ExpectedEffectiveness.HIGH,
        )
    link = link_risk_control(
        actor=manager,
        risk=risk,
        control_version=version,
        valid_from=timezone.localdate() - timedelta(days=1),
        effectiveness_expected=ExpectedEffectiveness.HIGH,
    )
    review_control(
        actor=reviewer,
        risk_control=link,
        result=ControlReviewResult.EFFECTIVE,
        notes="Control sintético operando según diseño.",
        next_review_date=timezone.localdate() + timedelta(days=30),
    )
    risk = close_risk(actor=approver, risk=risk, reason="Residual bajo y control vigente")
    assert risk.status == RiskStatus.CLOSED
    assert AuditEvent.objects.filter(action="risk.closed", object_id=risk.pk).exists()
    assert risk_alert_status(risk=risk) == "not_applicable"
    risk = reopen_risk(actor=manager, risk=risk, reason="Cambio sintético del proceso")
    assert risk.status == RiskStatus.REOPENED


def test_high_residual_requires_current_controls(
    admin_user: User, organization: Organization, area: Area
) -> None:
    manager, owner, _reviewer, approver = risk_actors(admin_user, "HIGH")
    process = process_for_risk(
        admin_user=admin_user, organization=organization, area=area, suffix="HIGH"
    )
    risk = create_risk(
        actor=manager,
        organization=organization,
        process=process,
        code="RSK-HIGH",
        cause="Causa sintética.",
        event="Evento sintético.",
        consequence="Consecuencia sintética.",
        owner=owner,
    )
    assessment = create_risk_assessment(
        actor=manager,
        risk=risk,
        probability=5,
        impact=5,
        residual_probability=4,
        residual_impact=4,
        next_review_date=timezone.localdate() + timedelta(days=30),
    )
    submit_risk_assessment(actor=manager, assessment=assessment)
    approve_risk_assessment(
        actor=approver, assessment=assessment, reason="Riesgo alto confirmado"
    )
    with pytest.raises(ValidationError, match="RN-026"):
        accept_residual_risk(
            actor=approver,
            risk=risk,
            reason="Aceptación sin controles no permitida",
        )
    with pytest.raises(ValidationError, match="alto o crítico"):
        close_risk(actor=approver, risk=risk, reason="Cierre prematuro")
    assert risk_alert_status(risk=risk) == "treatment_required"


def test_control_alerts_cover_pending_ineffective_and_upcoming(
    admin_user: User, organization: Organization, area: Area
) -> None:
    manager, owner, reviewer, approver = risk_actors(admin_user, "ALERT")
    process = process_for_risk(
        admin_user=admin_user, organization=organization, area=area, suffix="ALERT"
    )
    risk = create_risk(
        actor=manager,
        organization=organization,
        process=process,
        code="RSK-ALERT",
        cause="Causa sintética.",
        event="Evento sintético.",
        consequence="Consecuencia sintética.",
        owner=owner,
    )
    control = create_control(
        actor=manager,
        organization=organization,
        code="CTL-ALERT",
        name="Control sintético",
        owner=owner,
    )
    version = create_control_version(
        actor=manager,
        control=control,
        description="Descripción ficticia del control.",
        control_type=ControlType.DETECTIVE,
        frequency=ControlFrequency.MONTHLY,
    )
    submit_control_version(actor=manager, version=version)
    version = approve_control_version(
        actor=approver,
        version=version,
        valid_from=timezone.localdate(),
        reason="Control conforme",
    )
    link = link_risk_control(
        actor=manager,
        risk=risk,
        control_version=version,
        valid_from=timezone.localdate(),
        effectiveness_expected=ExpectedEffectiveness.MEDIUM,
    )
    assert control_alert_status(link=link) == "pending_review"
    review_control(
        actor=reviewer,
        risk_control=link,
        result=ControlReviewResult.INEFFECTIVE,
        notes="El control sintético no alcanzó el resultado.",
        next_review_date=timezone.localdate() + timedelta(days=5),
    )
    assert control_alert_status(link=link) == "ineffective"
    replacement = create_control_version(
        actor=manager,
        control=control,
        description="Segunda versión ficticia del control.",
        control_type=ControlType.DETECTIVE,
        frequency=ControlFrequency.MONTHLY,
    )
    submit_control_version(actor=manager, version=replacement)
    approve_control_version(
        actor=approver,
        version=replacement,
        valid_from=timezone.localdate() + timedelta(days=1),
        reason="Sustitución controlada",
    )
    version.refresh_from_db()
    link.refresh_from_db()
    assert version.status == ControlVersionStatus.SUPERSEDED
    assert control_alert_status(link=link) == "ineffective"
    assert control_alert_status(
        link=link, on_date=timezone.localdate() + timedelta(days=1)
    ) == "not_applicable"
