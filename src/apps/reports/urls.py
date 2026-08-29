from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("export/<uuid:contract_id>/", views.export_contract, name="export-contract"),
]
