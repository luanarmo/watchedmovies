from django.urls import include, path

from .router import router

app_name = "users"

urlpatterns = [
    path("", include(router.urls)),
]
