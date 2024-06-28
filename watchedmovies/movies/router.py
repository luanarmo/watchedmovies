from rest_framework.routers import DefaultRouter

from .views import WatchedMovieViewSet

router = DefaultRouter()

router.register(r"watched-movies", WatchedMovieViewSet, basename="watched-movies")
