from __future__ import annotations

import pytest
from django.test import Client

from apps.accounts.models import Role, User


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
