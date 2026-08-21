from __future__ import annotations

from typing import cast
from uuid import UUID

from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.accounts.decorators import capability_required
from apps.accounts.models import User
from apps.accounts.policies import Capability

from .forms import ImportUploadForm
from .models import ImportJob, ImportTemplateVersion
from .selectors import import_job_detail, import_job_history, template_catalog
from .services import receive_and_validate_import, template_workbook


@capability_required(Capability.CREATE_IMPORTS)
def catalog(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "imports/catalog.html",
        {"templates": template_catalog(), "jobs": import_job_history()},
    )


@capability_required(Capability.CREATE_IMPORTS)
def download_template(request: HttpRequest, version_id: UUID) -> HttpResponse:
    try:
        version = ImportTemplateVersion.objects.select_related("template").get(pk=version_id)
        content = template_workbook(version)
    except (ImportTemplateVersion.DoesNotExist, ValidationError) as exc:
        raise Http404("Plantilla vigente no encontrada.") from exc
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{version.template.code}_v{version.version_no}.xlsx"'
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@capability_required(Capability.CREATE_IMPORTS)
def upload(request: HttpRequest) -> HttpResponse:
    form = ImportUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        uploaded = form.cleaned_data["file"]
        version = cast(ImportTemplateVersion, form.cleaned_data["template_version"])
        actor = cast(User, request.user)
        try:
            job = receive_and_validate_import(
                actor=actor,
                organization=version.template.organization,
                template_version=version,
                original_name=uploaded.name,
                content=uploaded.read(),
                synthetic_confirmed=bool(form.cleaned_data["synthetic_confirmed"]),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("imports:detail", job_id=job.pk)
    return render(request, "imports/upload.html", {"form": form})


@capability_required(Capability.CREATE_IMPORTS)
def detail(request: HttpRequest, job_id: UUID) -> HttpResponse:
    try:
        job = import_job_detail(job_id=job_id)
    except (ImportJob.DoesNotExist, ValueError) as exc:
        raise Http404("Carga no encontrada.") from exc
    return render(request, "imports/detail.html", {"job": job})
