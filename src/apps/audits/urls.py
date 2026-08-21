from django.urls import path

from . import views

app_name = "audits"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("<uuid:plan_id>/", views.detail, name="detail"),
]
