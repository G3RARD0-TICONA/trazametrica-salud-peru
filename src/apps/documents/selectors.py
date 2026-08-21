from django.db.models import Prefetch, QuerySet

from .models import Document, DocumentVersion, ReferenceSource, ReferenceVersion


def document_catalog() -> QuerySet[Document]:
    versions = DocumentVersion.objects.select_related("approved_by").order_by("-version_no")
    return (
        Document.objects.filter(is_active=True, organization__is_active=True)
        .select_related("organization", "responsible_area")
        .prefetch_related(Prefetch("versions", queryset=versions, to_attr="ordered_versions"))
        .order_by("code")
    )


def reference_catalog() -> QuerySet[ReferenceSource]:
    versions = ReferenceVersion.objects.select_related("approved_by").order_by("-version_no")
    return (
        ReferenceSource.objects.filter(is_active=True)
        .prefetch_related(Prefetch("versions", queryset=versions, to_attr="ordered_versions"))
        .order_by("code")
    )
