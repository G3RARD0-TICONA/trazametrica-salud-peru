from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Role, User, UserRole
from .policies import Capability, has_capability


def date_ranges_overlap(
    first_start: date,
    first_end: date | None,
    second_start: date,
    second_end: date | None,
) -> bool:
    return (first_end is None or second_start <= first_end) and (
        second_end is None or first_start <= second_end
    )


@transaction.atomic
def assign_role(
    *,
    actor: User,
    user: User,
    role: Role,
    valid_from: date,
    valid_to: date | None = None,
) -> UserRole:
    if not has_capability(actor, Capability.ASSIGN_ROLES):
        raise PermissionDenied("El actor no puede asignar roles.")
    if not actor.is_active or not user.is_active or not role.is_active:
        raise ValidationError("Actor, usuario y rol deben estar activos.")
    if valid_to is not None and valid_to < valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")

    assignments = UserRole.objects.select_for_update().filter(user=user, role=role)
    for assignment in assignments:
        if date_ranges_overlap(
            assignment.valid_from,
            assignment.valid_to,
            valid_from,
            valid_to,
        ):
            raise ValidationError("La asignación se superpone con otra vigencia.")

    return UserRole.objects.create(
        user=user,
        role=role,
        valid_from=valid_from,
        valid_to=valid_to,
        assigned_by=actor,
        created_by=actor,
        updated_by=actor,
    )


@transaction.atomic
def end_role_assignment(*, actor: User, assignment: UserRole, valid_to: date) -> UserRole:
    if not has_capability(actor, Capability.ASSIGN_ROLES):
        raise PermissionDenied("El actor no puede finalizar roles.")
    if valid_to < assignment.valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")
    assignments = UserRole.objects.select_for_update().filter(
        user=assignment.user,
        role=assignment.role,
    )
    locked = assignments.get(pk=assignment.pk)
    for other in assignments.exclude(pk=locked.pk):
        if date_ranges_overlap(locked.valid_from, valid_to, other.valid_from, other.valid_to):
            raise ValidationError("La nueva fecha final se superpone con otra vigencia.")
    locked.valid_to = valid_to
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["valid_to", "updated_by", "updated_at"])
    return locked


@transaction.atomic
def deactivate_user(*, actor: User, user: User, reason: str) -> User:
    if not has_capability(actor, Capability.MANAGE_USERS):
        raise PermissionDenied("El actor no puede desactivar usuarios.")
    if actor.pk == user.pk:
        raise ValidationError("No puede desactivar su propia cuenta.")
    if not reason.strip():
        raise ValidationError("La desactivación requiere un motivo.")
    locked = User.objects.select_for_update().get(pk=user.pk)
    locked.is_active = False
    locked.deactivated_at = timezone.now()
    locked.deactivated_by = actor
    locked.deactivation_reason = reason.strip()
    locked.updated_by = actor
    locked.full_clean()
    locked.save(
        update_fields=[
            "is_active",
            "deactivated_at",
            "deactivated_by",
            "deactivation_reason",
            "updated_by",
            "updated_at",
        ]
    )
    return locked
