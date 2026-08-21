from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.organizations.models import (
    Area,
    Organization,
    ResponsibilityAssignment,
    ResponsibilityType,
    Service,
    Site,
)
from apps.organizations.services import (
    assign_responsibility,
    create_area,
    create_organization,
    create_service,
    create_site,
    deactivate_master,
    end_responsibility,
    move_area,
    update_master_identity,
)

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_only_one_active_organization_is_allowed(admin_user: User) -> None:
    create_organization(actor=admin_user, code="ORG-UNO", name="Organización Sintética Uno")
    with pytest.raises(ValidationError, match="ya tiene"):
        create_organization(actor=admin_user, code="ORG-DOS", name="Organización Sintética Dos")


def test_codes_are_normalized_and_unique_inside_scope(
    admin_user: User,
    organization: Organization,
) -> None:
    first = create_site(
        actor=admin_user,
        organization=organization,
        code="  sede-a  ",
        name="Sede Sintética A",
    )
    assert first.code == "SEDE-A"
    with pytest.raises(ValidationError):
        create_site(
            actor=admin_user,
            organization=organization,
            code="SEDE-A",
            name="Sede Sintética Duplicada",
        )


def test_master_identity_can_be_updated_with_audited_actor(
    admin_user: User,
    site: Site,
) -> None:
    updated = update_master_identity(
        actor=admin_user,
        master=site,
        code="SED-NUEVA",
        name="Sede Sintética Actualizada",
    )
    assert updated.code == "SED-NUEVA"
    assert updated.updated_by == admin_user


def test_physical_delete_is_blocked_for_instance_and_queryset(site: Site) -> None:
    with pytest.raises(ValidationError, match="no se eliminan"):
        site.delete()
    with pytest.raises(ValidationError, match="no se eliminan"):
        Site.objects.filter(pk=site.pk).delete()
    assert Site.objects.filter(pk=site.pk).exists()


def test_parent_cannot_be_deactivated_before_active_children(
    admin_user: User,
    site: Site,
) -> None:
    service = create_service(
        actor=admin_user,
        site=site,
        code="SER-A",
        name="Servicio Sintético A",
    )
    with pytest.raises(ValidationError, match="servicios activos"):
        deactivate_master(actor=admin_user, master=site, reason="Reorganización sintética")
    inactive = deactivate_master(
        actor=admin_user,
        master=service,
        reason="Fin de catálogo sintético",
    )
    assert not inactive.is_active
    assert inactive.deactivated_by == admin_user


def test_area_move_rejects_hierarchy_cycle(
    admin_user: User,
    organization: Organization,
) -> None:
    root = create_area(
        actor=admin_user,
        organization=organization,
        code="RAIZ",
        name="Área Raíz Sintética",
    )
    child = create_area(
        actor=admin_user,
        organization=organization,
        code="HIJA",
        name="Área Hija Sintética",
        parent=root,
    )
    with pytest.raises(ValidationError, match="ciclo"):
        move_area(actor=admin_user, area=root, parent=child)


def test_responsibility_vigencies_do_not_overlap(
    admin_user: User,
    regular_user: User,
    area: Area,
) -> None:
    today = timezone.localdate()
    assignment = assign_responsibility(
        actor=admin_user,
        area=area,
        user=regular_user,
        responsibility_type=ResponsibilityType.AREA_OWNER,
        valid_from=today,
    )
    with pytest.raises(ValidationError, match="superpone"):
        assign_responsibility(
            actor=admin_user,
            area=area,
            user=regular_user,
            responsibility_type=ResponsibilityType.AREA_OWNER,
            valid_from=today + timedelta(days=1),
        )
    closed = end_responsibility(actor=admin_user, assignment=assignment, valid_to=today)
    assert closed.valid_to == today


def test_database_rejects_inverted_responsibility_dates(
    admin_user: User,
    regular_user: User,
    area: Area,
) -> None:
    today = timezone.localdate()
    with pytest.raises(IntegrityError), transaction.atomic():
        ResponsibilityAssignment.objects.create(
            area=area,
            user=regular_user,
            responsibility_type=ResponsibilityType.DATA_STEWARD,
            valid_from=today,
            valid_to=today - timedelta(days=1),
            created_by=admin_user,
            updated_by=admin_user,
        )


def test_non_privileged_user_cannot_mutate_catalog(
    regular_user: User,
    organization: Organization,
) -> None:
    with pytest.raises(PermissionDenied):
        create_site(
            actor=regular_user,
            organization=organization,
            code="DENEGADA",
            name="Sede que no debe crearse",
        )
    assert not Site.objects.filter(code="DENEGADA").exists()


def test_organization_cannot_deactivate_with_active_structure(
    admin_user: User,
    organization: Organization,
) -> None:
    create_area(
        actor=admin_user,
        organization=organization,
        code="ACTIVA",
        name="Área Sintética Activa",
    )
    with pytest.raises(ValidationError, match="sedes y áreas"):
        deactivate_master(
            actor=admin_user,
            master=organization,
            reason="Cierre sintético",
        )


def test_invalid_timezone_and_real_data_label_are_rejected(admin_user: User) -> None:
    with pytest.raises(ValidationError):
        create_organization(
            actor=admin_user,
            code="ORG-ZONA",
            name="Organización Sintética",
            timezone_name="Zona/Inexistente",
        )
    with pytest.raises(ValidationError):
        create_organization(
            actor=admin_user,
            code="ORG-REAL",
            name="Organización Sintética",
            demo_label="ENTORNO REAL",
        )


def test_expected_p07_tables_are_created() -> None:
    assert Organization._meta.db_table == "organizations_organization"
    assert Site._meta.db_table == "organizations_site"
    assert Service._meta.db_table == "organizations_service"
    assert Area._meta.db_table == "organizations_area"
    assert (
        ResponsibilityAssignment._meta.db_table
        == "organizations_responsibility_assignment"
    )
