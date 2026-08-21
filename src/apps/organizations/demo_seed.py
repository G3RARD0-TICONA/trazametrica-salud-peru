from __future__ import annotations

import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.accounts.policies import Capability, has_capability

from .models import Area, Organization, Service, Site

DEMO_NAMESPACE = uuid.UUID("f59a753c-0896-5c9d-a490-c9ac0c1e0907")

SITE_CATALOG = (
    ("SED-01", "Sede Sintética Norte"),
    ("SED-02", "Sede Sintética Centro"),
    ("SED-03", "Sede Sintética Sur"),
)

SERVICE_COUNTS = {"SED-01": 7, "SED-02": 7, "SED-03": 6}

AREA_CATALOG = (
    ("DIR", "Dirección Sintética", None),
    ("CAL", "Calidad Sintética", "DIR"),
    ("OPE", "Operaciones Sintéticas", "DIR"),
    ("DAT", "Datos Sintéticos", "DIR"),
    ("LOG", "Logística Sintética", "OPE"),
    ("PLA", "Planeamiento Sintético", "OPE"),
    ("AUD", "Auditoría Sintética", "CAL"),
    ("MEJ", "Mejora Sintética", "CAL"),
    ("KPI", "Indicadores Sintéticos", "DAT"),
    ("SIS", "Sistemas Sintéticos", "DAT"),
    ("DOC", "Gestión Documental Sintética", "CAL"),
    ("RIE", "Riesgos Sintéticos", "CAL"),
)


def demo_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


@transaction.atomic
def seed_organization_catalog(*, actor: User) -> dict[str, int]:
    if not actor.is_active or not has_capability(actor, Capability.MANAGE_ORGANIZATION):
        raise PermissionDenied("El actor no puede generar el catálogo organizacional.")

    organization = Organization.objects.filter(pk=demo_uuid("organization:demo")).first()
    if organization is None:
        if Organization.objects.filter(is_active=True).exists():
            raise ValidationError("La instalación ya contiene otra organización activa.")
        organization = Organization(
            id=demo_uuid("organization:demo"),
            code="ORG-DEMO",
            name="Organización Demostrativa Trazamétrica",
            timezone="America/Lima",
            demo_label="DATOS SINTÉTICOS — NO USAR EN ATENCIÓN REAL",
            created_by=actor,
            updated_by=actor,
        )
    elif not organization.is_active:
        raise ValidationError("La organización sintética existe, pero está inactiva.")
    else:
        organization.code = "ORG-DEMO"
        organization.name = "Organización Demostrativa Trazamétrica"
        organization.timezone = "America/Lima"
        organization.demo_label = "DATOS SINTÉTICOS — NO USAR EN ATENCIÓN REAL"
        organization.updated_by = actor
    organization.full_clean()
    organization.save()

    sites: dict[str, Site] = {}
    for site_code, site_name in SITE_CATALOG:
        site = Site.objects.filter(pk=demo_uuid(f"site:{site_code}")).first()
        if site is None:
            site = Site(
                id=demo_uuid(f"site:{site_code}"),
                organization=organization,
                code=site_code,
                name=site_name,
                created_by=actor,
                updated_by=actor,
            )
        else:
            site.organization = organization
            site.code = site_code
            site.name = site_name
            site.updated_by = actor
        site.full_clean()
        site.save()
        sites[site_code] = site

    service_number = 1
    for site_code, count in SERVICE_COUNTS.items():
        site = sites[site_code]
        for _ in range(count):
            service_code = f"SER-{service_number:02d}"
            service = Service.objects.filter(
                pk=demo_uuid(f"service:{service_code}")
            ).first()
            if service is None:
                service = Service(
                    id=demo_uuid(f"service:{service_code}"),
                    site=site,
                    code=service_code,
                    name=f"Servicio Sintético {service_number:02d}",
                    created_by=actor,
                    updated_by=actor,
                )
            else:
                service.site = site
                service.code = service_code
                service.name = f"Servicio Sintético {service_number:02d}"
                service.updated_by = actor
            service.full_clean()
            service.save()
            service_number += 1

    areas: dict[str, Area] = {}
    for area_code, area_name, parent_code in AREA_CATALOG:
        parent = areas.get(parent_code) if parent_code else None
        area = Area.objects.filter(pk=demo_uuid(f"area:{area_code}")).first()
        if area is None:
            area = Area(
                id=demo_uuid(f"area:{area_code}"),
                organization=organization,
                parent=parent,
                code=area_code,
                name=area_name,
                created_by=actor,
                updated_by=actor,
            )
        else:
            area.organization = organization
            area.parent = parent
            area.code = area_code
            area.name = area_name
            area.updated_by = actor
        area.full_clean()
        area.save()
        areas[area_code] = area

    return {
        "organizations": Organization.objects.filter(pk=organization.pk).count(),
        "sites": Site.objects.filter(organization=organization).count(),
        "services": Service.objects.filter(site__organization=organization).count(),
        "areas": Area.objects.filter(organization=organization).count(),
    }
