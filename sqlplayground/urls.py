"""
URL configuration for the SQL Playground project.

The account routes are mounted at the site root so the login page lives at
/login/ instead of /accounts/login/. Lessons live under /lessons/, the free
sandbox under /sandbox/, and account management under /dashboard/.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from .views import custom_404, custom_500

handler404 = custom_404
handler500 = custom_500

urlpatterns = [
    path("", include("accounts.urls")),
    path("lessons/", include("lessons.urls")),
    path("sandbox/", include("dashboard.sandbox_urls")),
    path("dashboard/", include("dashboard.urls")),
]

# Serve uploaded media (profile photos) during local development only.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
