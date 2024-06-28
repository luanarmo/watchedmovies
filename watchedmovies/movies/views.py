from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from watchedmovies.movies.models import WatchedMovie

from .serializers import WatchedMovieSerializer


class WatchedMovieViewSet(viewsets.ModelViewSet):
    """Wiewset create, list, update, delete WatchedMovie"""

    serializer_class = WatchedMovieSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        return WatchedMovie.objects.filter(profile=self.request.user.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)
