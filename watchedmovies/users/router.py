from rest_framework.routers import DefaultRouter

from .views import AnonymousUserViewset, UserViewSet

router = DefaultRouter()

router.register(r"users", UserViewSet, basename="users")
router.register(r"anonymous", AnonymousUserViewset, basename="anonymous")
