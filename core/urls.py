from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Main project URLs
urlpatterns = [
    path("admin/", admin.site.urls),
    # Djoser Authentication URLs
    path("auth/", include("djoser.urls")),  # User management endpoints
    path("auth/", include("djoser.urls.jwt")),  # JWT token endpoints
    # Webinar App URLs
    path("", include("webinar.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
