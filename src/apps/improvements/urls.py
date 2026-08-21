from django.urls import path

from . import views

app_name = "improvements"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("<uuid:finding_id>/", views.detail, name="detail"),
]
