from django.urls import path

from . import views

app_name = "imports"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("upload/", views.upload, name="upload"),
    path("templates/<uuid:version_id>/download/", views.download_template, name="download"),
    path("jobs/<uuid:job_id>/", views.detail, name="detail"),
]
