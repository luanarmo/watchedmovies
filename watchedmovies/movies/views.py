from rest_framework import status
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import GenericViewSet

from watchedmovies.movies.models import ViewDetails, WatchedMovie

from ..pagination import CustomPagination
from . import filters, serializers, services


class WatchedMovieViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    """Wiewset list watched movies"""

    serializer_class = serializers.WatchedMovieSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    serializer_class = serializers.WatchedMovieSerializer
    pagination_class = CustomPagination
    filterset_class = filters.WatchedMovieFilter

    def get_queryset(self):
        profile = self.request.user.profile
        return WatchedMovie.objects.filter(view_details__profile=profile).distinct()

    def destroy(self, request, *args, **kwargs):
        watched_movie = self.get_object()
        services.destroy_view_detail(watched_movie=watched_movie)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ViewDetailViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin, UpdateModelMixin):
    """Wiewset create, list, update, delete ViewDetail"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    serializer_class = serializers.ListViewDetailSerializer
    pagination_class = CustomPagination
    filterset_class = filters.ViewDetailFilter

    def get_serializer_class(self):
        actions = {
            "list": serializers.ListViewDetailSerializer,
            "retrieve": serializers.ListViewDetailSerializer,
            "create": serializers.CreateViewDetailSerializer,
            "update": serializers.UpdateViewDetailSerializer,
            "partial_update": serializers.UpdateViewDetailSerializer,
        }
        return actions.get(self.action, serializers.DefaultSerializer)

    def get_queryset(self):
        return ViewDetails.objects.filter(profile=self.request.user.profile)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        view_detail = services.create_view_detail(**serializer.validated_data, profile=request.user.profile)
        return Response(serializers.ListViewDetailSerializer(view_detail).data, status=status.HTTP_201_CREATED)
