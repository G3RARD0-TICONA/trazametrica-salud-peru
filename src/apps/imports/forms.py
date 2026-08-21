from django import forms

from .models import ImportTemplateVersion, TemplateVersionStatus


class ImportUploadForm(forms.Form):
    template_version = forms.ModelChoiceField(
        label="Plantilla vigente",
        queryset=ImportTemplateVersion.objects.filter(
            status=TemplateVersionStatus.EFFECTIVE,
            template__is_active=True,
            template__organization__is_active=True,
        )
        .select_related("template")
        .order_by("template__code", "-version_no"),
    )
    file = forms.FileField(label="Archivo XLSX")
    synthetic_confirmed = forms.BooleanField(
        label="Confirmo que contiene únicamente DATOS SINTÉTICOS",
        required=True,
    )
