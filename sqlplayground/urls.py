"""
URL configuration for the SQL Playground project.

The account routes are mounted at the site root so the login page lives at
/login/ instead of /accounts/login/. Dashboard routes live under /dashboard/.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
]

# Serve uploaded media (profile photos) during local development only.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
