from uuid import UUID

from django.db.models import Prefetch, QuerySet

from .models import Process, ProcessVersion, SipocEntry


def process_catalog() -> QuerySet[Process]:
    versions = ProcessVersion.objects.select_related("approved_by").order_by("-version_no")
    return (
        Process.objects.filter(is_active=True, organization__is_active=True)
        .select_related("organization", "owner_area")
        .prefetch_related(Prefetch("versions", queryset=versions, to_attr="ordered_versions"))
        .order_by("process_type", "code")
    )


def process_detail(*, process_id: UUID) -> Process:
    entries = SipocEntry.objects.order_by("entry_type", "position")
    versions = ProcessVersion.objects.select_related(
        "created_by",
        "approved_by",
    ).prefetch_related(Prefetch("sipoc_entries", queryset=entries, to_attr="ordered_sipoc"))
    return (
        Process.objects.filter(is_active=True, organization__is_active=True)
        .select_related("organization", "owner_area")
        .prefetch_related(Prefetch("versions", queryset=versions, to_attr="ordered_versions"))
        .get(pk=process_id)
    )
