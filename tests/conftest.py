from __future__ import annotations

import pytest
from django.test import Client

from apps.accounts.models import Role, User
from apps.organizations.models import Area, Organization, Site
from apps.organizations.services import create_area, create_organization, create_site


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def admin_user(db: None) -> User:
    return User.objects.create_superuser(
        username="admin_sintetico",
        password="Clave-Sintetica-2026",
        email="admin@example.invalid",
    )


@pytest.fixture
def regular_user(db: None, admin_user: User) -> User:
    return User.objects.create_user(
        username="analista_sintetico",
        password="Clave-Sintetica-2026",
        email="analista@example.invalid",
        created_by=admin_user,
        updated_by=admin_user,
    )


@pytest.fixture
def viewer_role(db: None, admin_user: User) -> Role:
    return Role.objects.create(
        code="viewer",
        name="Consulta",
        description="Rol sintético de consulta.",
        created_by=admin_user,
        updated_by=admin_user,
    )


@pytest.fixture
def organization(db: None, admin_user: User) -> Organization:
    return create_organization(
        actor=admin_user,
        code="ORG-TEST",
        name="Organización Sintética de Prueba",
    )


@pytest.fixture
def site(db: None, admin_user: User, organization: Organization) -> Site:
    return create_site(
        actor=admin_user,
        organization=organization,
        code="SED-TEST",
        name="Sede Sintética de Prueba",
    )


@pytest.fixture
def area(db: None, admin_user: User, organization: Organization) -> Area:
    return create_area(
        actor=admin_user,
        organization=organization,
        code="AREA-TEST",
        name="Área Sintética de Prueba",
    )
