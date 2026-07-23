from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django_smartbase_admin.admin.site import sb_admin_site
from config.sbadmin_registry import register_retoucher_admins
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "مدیریت ریتاچر"
admin.site.site_title = "پنل مدیریت ریتاچر"
admin.site.index_title = "مدیریت سامانه"

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)




# Register all existing Retoucher ModelAdmin classes before evaluating
# sb_admin_site.urls. SmartBase generates URL patterns from this registry.
register_retoucher_admins()
urlpatterns = [
    path("api/customer/", include("customer_membership.urls")),
    path("django-admin/", admin.site.urls),
    path("panel/", include("control_panel.urls")),
    path("admin/", RedirectView.as_view(pattern_name="control_panel:dashboard", permanent=False)),
    path("system-admin/", RedirectView.as_view(pattern_name="control_panel:backend_modules", permanent=False), name="system-admin"),
    path("smartbase-admin/", sb_admin_site.urls),
    path("accounts/", include("allauth.urls")),


    path("i18n/", include("django.conf.urls.i18n")),
    path("ckeditor/", include("ckeditor_uploader.urls")),

    path("api/catalog/", include("catalog.urls")),
    path("api/projects/", include("projects.urls")),
    # Notifications API
    path("api/", include("notifications.urls")),

    path("api/payments/", include("payments.urls")),

    # Accounts API
    path("api/accounts/", include("accounts.urls")),

    path("api/orders/", include("orders.dispute_urls")),
    path("api/orders/", include("orders.sla_urls")),
    path("api/", include("orders.order_urls")),

    # JWT Auth
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API schema and docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)