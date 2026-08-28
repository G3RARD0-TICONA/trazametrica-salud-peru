from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audits.models import Finding
from apps.improvements.models import CorrectiveAction
from apps.indicators.models import Indicator
from apps.organizations.models import Organization
from apps.processes.models import Process

from .models import (
    AssessmentStatus,
    Control,
    ControlFrequency,
    ControlReview,
    ControlReviewResult,
    ControlType,
    ControlVersion,
    ControlVersionStatus,
    ExpectedEffectiveness,
    Risk,
    RiskActionLink,
    RiskAssessment,
    RiskControl,
    RiskFindingLink,
    RiskIndicatorLink,
    RiskStatus,
    risk_level_for,
)

DEMO_NAMESPACE = uuid.UUID("94201b9c-a7c1-5b0d-8893-28cf6bb3f77d")
DEMO_CUTOFF = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def demo_risk_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


def _demo_user(*, actor: User, key: str, username: str, first_name: str) -> User:
    user, created = User.objects.get_or_create(
        id=demo_risk_uuid(f"user:{key}"),
        defaults={
            "username": username,
            "email": f"{username}@example.invalid",
            "first_name": first_name,
            "last_name": "Riesgos Sintéticos",
            "created_by": actor,
            "updated_by": actor,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


def _assessment_values(index: int, version_no: int) -> tuple[int, int, int, int]:
    probability = 5 - (index % 4)
    impact = 5 - (index % 3)
    reduction = 2 if version_no == 2 else 1
    residual_probability = max(1, probability - reduction)
    residual_impact = max(1, impact - 1)
    return probability, impact, residual_probability, residual_impact


@transaction.atomic
def seed_risks(*, actor: User, dataset_version: str = "1") -> dict[str, int]:
    if dataset_version != "1":
        raise ValidationError("La versión de semilla de riesgos no está soportada.")
    organization = Organization.objects.filter(is_active=True).get()
    processes = list(
        Process.objects.filter(organization=organization, is_active=True).order_by("code")[:20]
    )
    indicators = list(
        Indicator.objects.filter(organization=organization, is_active=True).order_by("code")[:20]
    )
    findings = list(Finding.objects.order_by("code")[:12])
    actions = list(CorrectiveAction.objects.order_by("code")[:12])
    if len(processes) != 20 or len(indicators) != 20:
        raise ValidationError("Ejecute primero las semillas P09 y P11.")
    if len(findings) != 12 or len(actions) != 12:
        raise ValidationError("Ejecute primero las semillas P12 y P13.")

    owner = _demo_user(
        actor=actor,
        key="owner",
        username="responsable_riesgos_demo",
        first_name="Responsable",
    )
    reviewer = _demo_user(
        actor=actor,
        key="reviewer",
        username="revisor_riesgos_demo",
        first_name="Revisor",
    )
    approver = _demo_user(
        actor=actor,
        key="approver",
        username="aprobador_riesgos_demo",
        first_name="Aprobador",
    )

    controls: list[ControlVersion] = []
    for index in range(12):
        number = index + 1
        control, _ = Control.objects.get_or_create(
            id=demo_risk_uuid(f"control:{number:03d}"),
            defaults={
                "organization": organization,
                "code": f"CTL-{number:03d}",
                "name": f"Control administrativo sintético {number:03d}",
                "owner": owner,
                "created_by": actor,
                "updated_by": actor,
            },
        )
        version, _ = ControlVersion.objects.get_or_create(
            id=demo_risk_uuid(f"control-version:{number:03d}:1"),
            defaults={
                "control": control,
                "version_no": 1,
                "status": ControlVersionStatus.EFFECTIVE,
                "description": f"Ejecución verificable ficticia del control {number:03d}.",
                "control_type": (
                    ControlType.PREVENTIVE if index % 2 == 0 else ControlType.DETECTIVE
                ),
                "frequency": ControlFrequency.MONTHLY,
                "valid_from": date(2026, 1, 1),
                "submitted_at": DEMO_CUTOFF,
                "submitted_by": actor,
                "approved_at": DEMO_CUTOFF,
                "approved_by": approver,
                "decision_reason": "Control sintético aprobado para demostración.",
                "created_by": actor,
                "updated_by": approver,
            },
        )
        controls.append(version)

    risks: list[Risk] = []
    for index, process in enumerate(processes):
        number = index + 1
        risk, _ = Risk.objects.get_or_create(
            id=demo_risk_uuid(f"risk:{number:03d}"),
            defaults={
                "organization": organization,
                "process": process,
                "code": f"RSK-{number:03d}",
                "cause": f"Causa administrativa sintética {number:03d}.",
                "event": f"Evento de riesgo ficticio {number:03d}.",
                "consequence": f"Consecuencia administrativa sintética {number:03d}.",
                "owner": owner,
                "status": RiskStatus.CONTROLLED,
                "created_by": actor,
                "updated_by": approver,
            },
        )
        risks.append(risk)
        version_total = 2 if index < 4 else 1
        for version_no in range(1, version_total + 1):
            probability, impact, residual_probability, residual_impact = _assessment_values(
                index, version_no
            )
            inherent_level = probability * impact
            residual_level = residual_probability * residual_impact
            is_prior = version_total == 2 and version_no == 1
            assessment, _ = RiskAssessment.objects.get_or_create(
                id=demo_risk_uuid(f"assessment:{number:03d}:{version_no}"),
                defaults={
                    "risk": risk,
                    "version_no": version_no,
                    "status": (
                        AssessmentStatus.SUPERSEDED
                        if is_prior
                        else AssessmentStatus.APPROVED
                    ),
                    "probability": probability,
                    "impact": impact,
                    "inherent_level": inherent_level,
                    "inherent_band": risk_level_for(inherent_level),
                    "residual_probability": residual_probability,
                    "residual_impact": residual_impact,
                    "residual_level": residual_level,
                    "residual_band": risk_level_for(residual_level),
                    "assessed_at": DEMO_CUTOFF + timedelta(days=version_no),
                    "next_review_date": (
                        date(2026, 8, 20)
                        if index % 3 == 0
                        else date(2026, 8, 25)
                        if index % 3 == 1
                        else date(2026, 10, 1)
                    ),
                    "submitted_at": DEMO_CUTOFF + timedelta(days=version_no),
                    "submitted_by": actor,
                    "approved_at": DEMO_CUTOFF + timedelta(days=version_no, hours=1),
                    "approved_by": approver,
                    "decision_reason": "Evaluación sintética aprobada.",
                    "created_by": actor,
                    "updated_by": approver,
                },
            )
            if not is_prior:
                risk.status = (
                    RiskStatus.CONTROLLED
                    if int(assessment.residual_level or 25) <= 9
                    else RiskStatus.UNDER_TREATMENT
                )
                risk.updated_by = approver
                risk.save(update_fields=["status", "updated_by", "updated_at"])
        RiskIndicatorLink.objects.get_or_create(
            id=demo_risk_uuid(f"risk-indicator:{number:03d}"),
            defaults={
                "risk": risk,
                "indicator": indicators[index],
                "created_by": actor,
                "updated_by": actor,
            },
        )
        if index < 12:
            RiskFindingLink.objects.get_or_create(
                id=demo_risk_uuid(f"risk-finding:{number:03d}"),
                defaults={
                    "risk": risk,
                    "finding": findings[index],
                    "created_by": actor,
                    "updated_by": actor,
                },
            )
            RiskActionLink.objects.get_or_create(
                id=demo_risk_uuid(f"risk-action:{number:03d}"),
                defaults={
                    "risk": risk,
                    "action": actions[index],
                    "created_by": actor,
                    "updated_by": actor,
                },
            )

    for index in range(24):
        risk = risks[index % len(risks)]
        control_version = controls[index % len(controls)]
        link, _ = RiskControl.objects.get_or_create(
            id=demo_risk_uuid(f"risk-control:{index + 1:03d}"),
            defaults={
                "risk": risk,
                "control_version": control_version,
                "valid_from": date(2026, 1, 1) + timedelta(days=index),
                "effectiveness_expected": ExpectedEffectiveness.HIGH,
                "created_by": actor,
                "updated_by": actor,
            },
        )
        if index < 18:
            ControlReview.objects.get_or_create(
                id=demo_risk_uuid(f"control-review:{index + 1:03d}"),
                defaults={
                    "risk_control": link,
                    "reviewer": reviewer,
                    "reviewed_at": DEMO_CUTOFF + timedelta(days=index),
                    "result": (
                        ControlReviewResult.INEFFECTIVE
                        if index % 7 == 0
                        else ControlReviewResult.EFFECTIVE
                    ),
                    "notes": "Revisión de control con datos exclusivamente sintéticos.",
                    "next_review_date": date(2026, 9, 15) + timedelta(days=index),
                    "created_by": reviewer,
                    "updated_by": reviewer,
                },
            )

    return {
        "risks": Risk.objects.filter(organization=organization).count(),
        "assessments": RiskAssessment.objects.filter(
            risk__organization=organization
        ).count(),
        "controls": Control.objects.filter(organization=organization).count(),
        "control_versions": ControlVersion.objects.filter(
            control__organization=organization
        ).count(),
        "risk_controls": RiskControl.objects.filter(
            risk__organization=organization
        ).count(),
        "reviews": ControlReview.objects.filter(
            risk_control__risk__organization=organization
        ).count(),
        "indicator_links": RiskIndicatorLink.objects.filter(
            risk__organization=organization
        ).count(),
        "finding_links": RiskFindingLink.objects.filter(
            risk__organization=organization
        ).count(),
        "action_links": RiskActionLink.objects.filter(
            risk__organization=organization
        ).count(),
    }
