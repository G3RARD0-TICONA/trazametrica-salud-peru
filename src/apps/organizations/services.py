from __future__ import annotations

from datetime import date
from typing import TypeAlias

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability
from apps.accounts.services import date_ranges_overlap

from .models import (
    Area,
    Organization,
    ResponsibilityAssignment,
    ResponsibilityType,
    Service,
    Site,
)

Master: TypeAlias = Organization | Site | Service | Area


def _require_management(actor: User) -> None:
    if not actor.is_active or not has_capability(actor, Capability.MANAGE_ORGANIZATION):
        raise PermissionDenied("El actor no puede gestionar maestros organizacionales.")


def _validate_parent(*, organization: Organization, parent: Area | None) -> None:
    if parent is not None and parent.organization_id != organization.pk:
        raise ValidationError("El área padre debe pertenecer a la misma organización.")


@transaction.atomic
def create_organization(
    *,
    actor: User,
    code: str,
    name: str,
    timezone_name: str = "America/Lima",
    demo_label: str = "DATOS SINTÉTICOS",
) -> Organization:
    _require_management(actor)
    Organization.objects.select_for_update().filter(is_active=True).exists()
    if Organization.objects.filter(is_active=True).exists():
        raise ValidationError("La instalación ya tiene una organización activa.")
    organization = Organization(
        code=code,
        name=name,
        timezone=timezone_name,
        demo_label=demo_label,
        created_by=actor,
        updated_by=actor,
    )
    organization.full_clean()
    organization.save()
    return organization


@transaction.atomic
def create_site(*, actor: User, organization: Organization, code: str, name: str) -> Site:
    _require_management(actor)
    if not organization.is_active:
        raise ValidationError("La organización debe estar activa.")
    site = Site(
        organization=organization,
        code=code,
        name=name,
        created_by=actor,
        updated_by=actor,
    )
    site.full_clean()
    site.save()
    return site


@transaction.atomic
def create_service(*, actor: User, site: Site, code: str, name: str) -> Service:
    _require_management(actor)
    if not site.is_active or not site.organization.is_active:
        raise ValidationError("La sede y su organización deben estar activas.")
    service = Service(
        site=site,
        code=code,
        name=name,
        created_by=actor,
        updated_by=actor,
    )
    service.full_clean()
    service.save()
    return service


@transaction.atomic
def create_area(
    *,
    actor: User,
    organization: Organization,
    code: str,
    name: str,
    parent: Area | None = None,
) -> Area:
    _require_management(actor)
    if not organization.is_active:
        raise ValidationError("La organización debe estar activa.")
    _validate_parent(organization=organization, parent=parent)
    area = Area(
        organization=organization,
        parent=parent,
        code=code,
        name=name,
        created_by=actor,
        updated_by=actor,
    )
    area.full_clean()
    area.save()
    return area


@transaction.atomic
def update_master_identity(*, actor: User, master: Master, code: str, name: str) -> Master:
    _require_management(actor)
    if not master.is_active:
        raise ValidationError("No se edita un maestro inactivo.")
    master.code = code
    master.name = name
    master.updated_by = actor
    master.full_clean()
    master.save(update_fields=["code", "name", "updated_by", "updated_at"])
    return master


@transaction.atomic
def move_area(*, actor: User, area: Area, parent: Area | None) -> Area:
    _require_management(actor)
    _validate_parent(organization=area.organization, parent=parent)
    if parent is not None:
        if parent.pk == area.pk:
            raise ValidationError("Un área no puede ser su propio padre.")
        ancestor = parent
        visited: set[object] = set()
        while ancestor is not None:
            if ancestor.pk == area.pk:
                raise ValidationError("El movimiento crearía un ciclo en la jerarquía.")
            if ancestor.pk in visited:
                raise ValidationError("La jerarquía existente contiene un ciclo.")
            visited.add(ancestor.pk)
            ancestor = ancestor.parent
    locked = Area.objects.select_for_update().get(pk=area.pk)
    locked.parent = parent
    locked.updated_by = actor
    locked.full_clean()
    locked.save(update_fields=["parent", "updated_by", "updated_at"])
    return locked


@transaction.atomic
def assign_responsibility(
    *,
    actor: User,
    area: Area,
    user: User,
    responsibility_type: ResponsibilityType,
    valid_from: date,
    valid_to: date | None = None,
) -> ResponsibilityAssignment:
    _require_management(actor)
    if not area.is_active or not user.is_active:
        raise ValidationError("El área y el usuario deben estar activos.")
    if valid_to is not None and valid_to < valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")
    assignments = ResponsibilityAssignment.objects.select_for_update().filter(
        area=area,
        user=user,
        responsibility_type=responsibility_type,
    )
    for assignment in assignments:
        if date_ranges_overlap(
            assignment.valid_from,
            assignment.valid_to,
            valid_from,
            valid_to,
        ):
            raise ValidationError("La responsabilidad se superpone con otra vigencia.")
    result = ResponsibilityAssignment(
        area=area,
        user=user,
        responsibility_type=responsibility_type,
        valid_from=valid_from,
        valid_to=valid_to,
        created_by=actor,
        updated_by=actor,
    )
    result.full_clean()
    result.save()
    return result


@transaction.atomic
def end_responsibility(
    *,
    actor: User,
    assignment: ResponsibilityAssignment,
    valid_to: date,
) -> ResponsibilityAssignment:
    _require_management(actor)
    if valid_to < assignment.valid_from:
        raise ValidationError("La fecha final no puede preceder a la inicial.")
    assignments = ResponsibilityAssignment.objects.select_for_update().filter(
        area=assignment.area,
        user=assignment.user,
        responsibility_type=assignment.responsibility_type,
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
def deactivate_master(*, actor: User, master: Master, reason: str) -> Master:
    _require_management(actor)
    if not reason.strip():
        raise ValidationError("La desactivación requiere un motivo.")
    locked = master.__class__.objects.select_for_update().get(pk=master.pk)
    if not locked.is_active:
        raise ValidationError("El maestro ya está inactivo.")
    today = timezone.localdate()
    if isinstance(locked, Organization) and (
        locked.sites.filter(is_active=True).exists() or locked.areas.filter(is_active=True).exists()
    ):
        raise ValidationError("Desactive primero las sedes y áreas activas.")
    if isinstance(locked, Site) and locked.services.filter(is_active=True).exists():
        raise ValidationError("Desactive primero los servicios activos de la sede.")
    if isinstance(locked, Area):
        has_current_assignments = locked.responsibility_assignments.filter(
            valid_from__lte=today,
        ).filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=today))
        if locked.children.filter(is_active=True).exists() or has_current_assignments.exists():
            raise ValidationError("Finalice responsabilidades y desactive las áreas hijas primero.")
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
