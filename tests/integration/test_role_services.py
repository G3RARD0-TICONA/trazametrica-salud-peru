from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import Role, User, UserRole
from apps.accounts.services import assign_role, deactivate_user, end_role_assignment

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_ordinary_user_requires_a_creator() -> None:
    with pytest.raises(ValueError, match="actor creador"):
        User.objects.create_user(username="sin_actor", password="Clave-Sintetica-2026")


def test_role_codes_are_normalized(
    admin_user: User,
) -> None:
    role = Role.objects.create(
        code="  auditor  ",
        name="Auditor",
        created_by=admin_user,
        updated_by=admin_user,
    )
    assert role.code == "AUDITOR"


def test_overlapping_assignment_is_rejected(
    admin_user: User,
    regular_user: User,
    viewer_role: Role,
) -> None:
    today = timezone.localdate()
    assign_role(
        actor=admin_user,
        user=regular_user,
        role=viewer_role,
        valid_from=today,
    )
    with pytest.raises(ValidationError, match="superpone"):
        assign_role(
            actor=admin_user,
            user=regular_user,
            role=viewer_role,
            valid_from=today + timedelta(days=1),
        )


def test_database_rejects_inverted_validity(
    admin_user: User,
    regular_user: User,
    viewer_role: Role,
) -> None:
    today = timezone.localdate()
    with pytest.raises(IntegrityError), transaction.atomic():
        UserRole.objects.create(
            user=regular_user,
            role=viewer_role,
            valid_from=today,
            valid_to=today - timedelta(days=1),
            assigned_by=admin_user,
            created_by=admin_user,
            updated_by=admin_user,
        )


def test_assignment_can_be_closed(
    admin_user: User,
    regular_user: User,
    viewer_role: Role,
) -> None:
    today = timezone.localdate()
    assignment = assign_role(
        actor=admin_user,
        user=regular_user,
        role=viewer_role,
        valid_from=today,
    )
    closed = end_role_assignment(actor=admin_user, assignment=assignment, valid_to=today)
    assert closed.valid_to == today
    assert closed.updated_by == admin_user


def test_non_privileged_user_cannot_assign_roles(
    admin_user: User,
    regular_user: User,
    viewer_role: Role,
) -> None:
    other = User.objects.create_user(
        username="otro_sintetico",
        password="Clave-Sintetica-2026",
        created_by=admin_user,
        updated_by=admin_user,
    )
    with pytest.raises(PermissionDenied):
        assign_role(
            actor=regular_user,
            user=other,
            role=viewer_role,
            valid_from=timezone.localdate(),
        )


def test_user_cannot_deactivate_self(admin_user: User) -> None:
    with pytest.raises(ValidationError, match="propia cuenta"):
        deactivate_user(actor=admin_user, user=admin_user, reason="Prueba sintética")
