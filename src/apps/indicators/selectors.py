from uuid import UUID

from django.db.models import Prefetch, QuerySet

from .models import Indicator, IndicatorResult, IndicatorVersion, ResultInput, ResultStatus


def indicator_catalog() -> QuerySet[Indicator]:
    versions = IndicatorVersion.objects.select_related("approved_by").order_by("-version_no")
    published = (
        IndicatorResult.objects.filter(status=ResultStatus.PUBLISHED)
        .select_related("site", "service")
        .order_by("-period_end", "-published_at")
    )
    return (
        Indicator.objects.filter(is_active=True, organization__is_active=True)
        .select_related("organization", "process", "owner")
        .prefetch_related(
            Prefetch("versions", queryset=versions, to_attr="ordered_versions"),
            Prefetch(
                "versions__results", queryset=published, to_attr="published_results"
            ),
        )
        .order_by("process__code", "code")
    )


def indicator_detail(*, indicator_id: UUID) -> Indicator:
    inputs = ResultInput.objects.select_related("observation").order_by("input_role", "position")
    results = (
        IndicatorResult.objects.select_related(
            "site", "service", "calculated_by", "published_by", "supersedes"
        )
        .prefetch_related(Prefetch("inputs", queryset=inputs, to_attr="ordered_inputs"))
        .order_by("-period_end", "-calculated_at")
    )
    versions = (
        IndicatorVersion.objects.select_related("approved_by")
        .prefetch_related(Prefetch("results", queryset=results, to_attr="ordered_results"))
        .order_by("-version_no")
    )
    return (
        Indicator.objects.filter(is_active=True, organization__is_active=True)
        .select_related("organization", "process", "owner")
        .prefetch_related(Prefetch("versions", queryset=versions, to_attr="ordered_versions"))
        .get(pk=indicator_id)
    )
