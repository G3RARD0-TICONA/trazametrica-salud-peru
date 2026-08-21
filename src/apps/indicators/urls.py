from django.urls import path

from . import views

app_name = "indicators"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("<uuid:indicator_id>/", views.detail, name="detail"),
]
