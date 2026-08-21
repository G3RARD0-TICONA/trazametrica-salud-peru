from django.urls import path

from . import views

app_name = "processes"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("<uuid:process_id>/", views.detail, name="detail"),
]
