from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("execute/<uuid:definition_id>/", views.execute, name="execute"),
    path("runs/<uuid:run_id>/", views.run_detail, name="run-detail"),
]
