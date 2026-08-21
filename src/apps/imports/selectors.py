from uuid import UUID

from django.db.models import Prefetch, QuerySet

from .models import ImportJob, ImportTemplate, ImportTemplateVersion, TemplateVersionStatus


def template_catalog() -> QuerySet[ImportTemplate]:
    versions = ImportTemplateVersion.objects.filter(
        status=TemplateVersionStatus.EFFECTIVE
    ).order_by("-version_no")
    return (
        ImportTemplate.objects.filter(is_active=True, organization__is_active=True)
        .select_related("organization")
        .prefetch_related(Prefetch("versions", queryset=versions, to_attr="effective_versions"))
        .order_by("code")
    )


def import_job_history() -> QuerySet[ImportJob]:
    return ImportJob.objects.select_related(
        "organization",
        "template_version__template",
        "created_by",
        "duplicate_of",
        "retry_of",
    ).order_by("-created_at")[:100]


def import_job_detail(*, job_id: UUID) -> ImportJob:
    return (
        ImportJob.objects.select_related(
            "organization",
            "template_version__template",
            "source_file",
            "created_by",
            "duplicate_of",
            "retry_of",
        )
        .prefetch_related("rows__errors")
        .get(pk=job_id)
    )
