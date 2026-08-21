from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", core_views.live, name="health-live"),
    path("health/ready/", core_views.ready, name="health-ready"),
    path("organization/", include("apps.organizations.urls")),
    path("documents/", include("apps.documents.urls")),
    path("processes/", include("apps.processes.urls")),
    path("imports/", include("apps.imports.urls")),
    path("", include("apps.accounts.urls")),
]
