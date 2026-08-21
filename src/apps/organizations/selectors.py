from __future__ import annotations

from django.db.models import Prefetch, QuerySet

from .models import Area, Organization, Service, Site


def active_organization_structure() -> Organization | None:
    active_services: QuerySet[Service] = Service.objects.filter(is_active=True).order_by("code")
    active_sites: QuerySet[Site] = (
        Site.objects.filter(is_active=True)
        .order_by("code")
        .prefetch_related(Prefetch("services", queryset=active_services))
    )
    active_areas: QuerySet[Area] = Area.objects.filter(is_active=True).order_by("code")
    return (
        Organization.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch("sites", queryset=active_sites),
            Prefetch("areas", queryset=active_areas),
        )
        .first()
    )
