from django.contrib import admin
from django.urls import include, path

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # =====================================================
    # DJANGO ADMIN
    # =====================================================

    path(
        "admin/",
        admin.site.urls
    ),

    # =====================================================
    # CUSTOM OWNER MANAGEMENT
    # =====================================================

    path(
        "management/",
        include("management.urls")
    ),

    # =====================================================
    # CUSTOMER STORE
    # =====================================================

    path(
        "",
        include("store.urls")
    ),
]


# =========================================================
# MEDIA FILES - DEVELOPMENT
# =========================================================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )