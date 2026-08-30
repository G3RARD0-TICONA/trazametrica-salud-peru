from __future__ import annotations

import statistics
import time

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.accounts.models import User
from apps.indicators.demo_seed import seed_indicators
from apps.organizations.demo_seed import seed_organization_catalog
from apps.processes.demo_seed import seed_processes

pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.performance]


def test_reference_catalogs_meet_p95_and_query_budgets(
    client: Client, admin_user: User
) -> None:
    if connection.vendor != "postgresql":
        pytest.skip("La referencia oficial de rendimiento usa PostgreSQL 17.")

    seed_organization_catalog(actor=admin_user)
    seed_processes(actor=admin_user)
    counts = seed_indicators(actor=admin_user, observation_count=100_000)
    assert counts == {"indicators": 200, "versions": 260, "observations": 100_000}

    client.force_login(admin_user)
    routes = (
        reverse("accounts:home"),
        reverse("organizations:structure"),
        reverse("processes:catalog"),
        reverse("indicators:catalog"),
        reverse("reports:dashboard"),
    )
    durations: list[float] = []
    for route in routes:
        for _ in range(4):
            started = time.perf_counter()
            with CaptureQueriesContext(connection) as queries:
                response = client.get(route)
            durations.append(time.perf_counter() - started)
            assert response.status_code == 200
            assert len(queries) <= 20, f"{route} ejecutó {len(queries)} consultas"

    p95 = statistics.quantiles(durations, n=100, method="inclusive")[94]
    assert p95 <= 2.0, f"p95 observado: {p95:.3f} s"
