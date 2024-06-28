from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from watchedmovies.users import urls

router = SimpleRouter()

if settings.DEBUG:
    router = DefaultRouter()


app_name = "api"
urlpatterns = urls.urlpatterns
