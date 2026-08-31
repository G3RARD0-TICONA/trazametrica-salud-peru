from __future__ import annotations

import uuid

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.urls import reverse

from apps.accounts.models import User
from apps.analytics.demo_seed import seed_analytics
from apps.analytics.models import AnalysisDefinition, AnalysisRun, AnalysisType, DefinitionStatus
from apps.analytics.services import (
    create_analysis_definition,
    publish_analysis_definition,
    run_analysis,
)
from apps.auditlog.models import AuditEvent
from apps.indicators.models import Indicator

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def _seed_dependencies(admin_user: User) -> None:
    call_command("seed_organizations_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_processes_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_import_templates_demo", actor=admin_user.username, dataset_version="1")
    call_command(
        "seed_indicators_demo",
        actor=admin_user.username,
        dataset_version="1",
        observation_count=5000,
    )


def test_definition_governance_run_reproducibility_seed_and_web(client, admin_user: User) -> None:
    _seed_dependencies(admin_user)
    indicator = Indicator.objects.order_by("code").first()
    assert indicator is not None
    definition = create_analysis_definition(
        actor=admin_user,
        code="ANA-TEST",
        name="Análisis sintético",
        analysis_type=AnalysisType.DESCRIPTIVE,
        target_indicator=indicator,
    )
    with pytest.raises(PermissionDenied, match="propia definición"):
        publish_analysis_definition(actor=admin_user, definition=definition)
    approver = User.objects.create_superuser(
        username="aprobador_analitica_test",
        password="Clave-Sintetica-2026",
        email="aprobador.analitica@example.invalid",
    )
    definition = publish_analysis_definition(actor=approver, definition=definition)
    assert definition.status == DefinitionStatus.PUBLISHED
    first = run_analysis(actor=admin_user, definition=definition)
    second = run_analysis(actor=admin_user, definition=definition)
    assert first.input_hash == second.input_hash
    assert first.output_hash == second.output_hash
    assert first.synthetic_confirmed is True
    assert first.assumptions["clinical_decision"] is False
    assert AuditEvent.objects.filter(action="analysis.executed", object_id=first.pk).exists()
    definition.name = "Cambio prohibido"
    with pytest.raises(ValidationError, match="inmutable"):
        definition.save()
    definition.refresh_from_db()
    replacement = create_analysis_definition(
        actor=admin_user,
        code="ANA-TEST",
        name="Análisis sintético v2",
        analysis_type=AnalysisType.DESCRIPTIVE,
        target_indicator=indicator,
    )
    assert replacement.version_no == 2
    publish_analysis_definition(actor=approver, definition=replacement)
    definition.refresh_from_db()
    assert definition.status == DefinitionStatus.SUPERSEDED

    seeded = seed_analytics(actor=admin_user)
    repeated = seed_analytics(actor=admin_user)
    assert seeded == repeated
    assert seeded["definitions"] == 6
    assert seeded["runs"] == 6
    call_command("seed_analytics_demo", actor=admin_user.username, dataset_version="1")
    call_command("seed_analytics_demo", actor=admin_user.username, dataset_version="1")
    with pytest.raises(ValidationError, match="versión de semilla"):
        seed_analytics(actor=admin_user, dataset_version="2")

    client.force_login(admin_user)
    response = client.get(reverse("analytics:catalog"))
    assert response.status_code == 200
    assert b"DATOS SINT" in response.content
    assert b"Configuraci\xc3\xb3n est\xc3\xa1ndar aprobada" in response.content
    assert b"{'window': 3}" not in response.content
    visual_titles = {
        "ANA-DESC-001": "Distribución y valores atípicos",
        "ANA-PARETO-001": "Pareto por servicio",
        "ANA-TREND-001": "Tendencia y media móvil",
        "ANA-LINEAR-001": "Regresión lineal: observado frente a estimado",
        "ANA-LOGISTIC-001": "Probabilidad estimada de cumplimiento",
    }
    for code, title in visual_titles.items():
        visual_run = AnalysisRun.objects.filter(definition__code=code).latest("executed_at")
        visual_detail = client.get(reverse("analytics:run-detail", args=[visual_run.pk]))
        visual_content = visual_detail.content.decode()
        assert visual_detail.status_code == 200
        assert title in visual_content
        assert "Resultados principales" in visual_content
        assert "Ver datos que respaldan el gráfico" in visual_content
        assert "<svg" in visual_content
    seeded_definition = AnalysisDefinition.objects.get(code="ANA-DESC-001")
    response = client.post(reverse("analytics:execute", args=[seeded_definition.pk]), {})
    assert response.status_code == 302
    assert AnalysisRun.objects.filter(definition=seeded_definition).count() == 2
    control_definition = AnalysisDefinition.objects.get(code="ANA-CONTROL-001")
    response = client.post(reverse("analytics:execute", args=[control_definition.pk]), {})
    assert response.status_code == 302
    detail = client.get(response["Location"])
    assert detail.status_code == 200
    assert "Gráfico de control" in detail.content.decode()
    assert b"<svg" in detail.content
    assert "Línea central" in detail.content.decode()
    assert "Resumen semanal en barras" in detail.content.decode()
    invalid = client.post(
        reverse("analytics:execute", args=[seeded_definition.pk]),
        {"period_start": "fecha-invalida"},
    )
    assert invalid.status_code == 400
    assert "AAAA-MM-DD" in invalid.content.decode()
    assert client.post(reverse("analytics:execute", args=[uuid.uuid4()]), {}).status_code == 404
    assert client.get(reverse("analytics:run-detail", args=[uuid.uuid4()])).status_code == 404


def test_analytics_catalog_denies_user_without_role(client, regular_user: User) -> None:
    client.force_login(regular_user)
    assert client.get(reverse("analytics:catalog")).status_code == 403
