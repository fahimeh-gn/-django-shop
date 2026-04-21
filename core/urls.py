from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerSplitView,
    SpectacularRedocView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    # Admin Panel
    path("admin/", admin.site.urls),

    # OpenAPI Schema (JSON)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI (local — no CDN)
    path(
        "api/docs/",
        SpectacularSwaggerSplitView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Redoc UI
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # Application Routes
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/cart/", include("apps.cart.urls")),
    path("api/orders/", include("apps.orders.urls")),



    # JWT urls
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),



]

# Static & Media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


