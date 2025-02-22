from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import token_refresh, token_verify

from watchedmovies.users.views import CustomTokenObtainPairView, VerifyEmailTokenView, VerifyResetPasswordTokenView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("watchedmovies.users.urls", namespace="users")),
    path("api/", include("watchedmovies.movies.urls", namespace="movies")),
    # User urls
    # path("api/", include("users.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    path("api/auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", token_refresh),
    path("api/auth/verify/", token_verify),
    path("api/auth/verify_email/<uid>/<token>/", VerifyEmailTokenView.as_view(), name="verify_email"),
    path("api/auth/reset_password/<uid>/<token>/", VerifyResetPasswordTokenView.as_view(), name="reset_password"),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
