from rest_framework.routers import DefaultRouter

from .views import PlanToWatchViewSet, TMDBViewSet, ViewDetailViewSet, WatchedMovieViewSet

router = DefaultRouter()

router.register(r"watched-movies", WatchedMovieViewSet, basename="watched-movies")
router.register(r"view-details", ViewDetailViewSet, basename="view-details")
router.register(r"tmdb", TMDBViewSet, basename="tmdb")
router.register(r"plan-to-watch", PlanToWatchViewSet, basename="plan-to-watch")
