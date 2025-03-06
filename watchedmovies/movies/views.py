from django.db.models import Max
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import GenericViewSet

from watchedmovies.movies.models import PlanToWatch, ViewDetails, WatchedMovie

from ..pagination import CustomPagination
from ..services import tmdb_api
from . import filters as custom_filters
from . import serializers, services


class WatchedMovieViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    """Wiewset list watched movies"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = custom_filters.WatchedMovieFilter
    ordering_fields = ["first_watched_date", "title"]
    ordering = ["-first_watched_date"]

    def get_serializer_class(self):
        actions = {
            "list": serializers.ListWatchedMovieSerializer,
            "retrieve": serializers.WatchedMovieSerializer,
        }
        return actions.get(self.action, serializers.DefaultSerializer)

    def get_queryset(self):
        profile = self.request.user.profile
        return WatchedMovie.objects.filter(view_details__profile=profile).annotate(
            first_watched_date=Max("view_details__watched_date")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        profile = request.user.profile
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"profile": profile})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={"profile": profile})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"profile": request.user.profile})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a watched movie"""
        watched_movie = self.get_object()
        profile = request.user.profile
        services.destroy_view_detail(watched_movie=watched_movie, profile=profile)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["GET"])
    def posters(self, request, year: str = None, ordering: str = None, *args, **kwargs):
        """Get posters from watched movies"""
        queryset = self.filter_queryset(self.get_queryset())
        collage = services.create_collage(queryset=queryset)
        response = HttpResponse(collage, content_type="image/jpeg")
        response["Content-Disposition"] = 'attachment; filename="collage.jpg"'
        return response

    @action(detail=False, methods=["GET"])
    def years(self, request, *args, **kwargs):
        """Get years from watched movies"""
        profile = request.user.profile
        years = services.get_watched_register_years(profile=profile)
        return Response(years, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"])
    def wrapped(self, request, *args, **kwargs):
        """Get statistics from watched movies"""
        profile = request.user.profile
        wrapped = services.create_wrapped(profile=profile)
        response = HttpResponse(wrapped, content_type="image/png")
        response["Content-Disposition"] = 'attachment; filename="wrapped.png"'
        return response


class ViewDetailViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin, UpdateModelMixin):
    """Wiewset create, list, update, delete ViewDetail"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    serializer_class = serializers.ListViewDetailSerializer
    pagination_class = CustomPagination
    filterset_class = custom_filters.ViewDetailFilter

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
        """Create a ViewDetail"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        view_detail = services.create_view_detail(**serializer.validated_data, profile=request.user.profile)
        return Response(serializers.ListViewDetailSerializer(view_detail).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Delete a ViewDetail"""
        view = self.get_object()
        view.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TMDBViewSet(GenericViewSet):
    """Viewset for TMDB API"""

    throttle_classes = [AnonRateThrottle]
    permission_classes = [AllowAny]
    serializer_class = serializers.ListTMDBMovieSerializer

    def get_queryset(self):
        pass

    @action(detail=False, methods=["GET"], url_path="movie-details/(?P<movie_id>[^/.]+)")
    def movie_details(self, request, movie_id: int = None, *args, **kwargs):
        """Get movie details"""
        movie_details = tmdb_api.get_movie_details(movie_id)
        serialized = serializers.ListTMDBMovieSerializer(data=movie_details)
        serialized.is_valid(raise_exception=True)

        return Response(serialized.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"])
    def popular_movies(self, request, *args, **kwargs):
        """Get popular movies"""
        popular_movies = tmdb_api.get_popular_movies()
        serialized = serializers.ListTMDBMovieSerializer(data=popular_movies["results"], many=True)
        serialized.is_valid(raise_exception=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="search-movies/(?P<query>[^/.]+)")
    def search_movies(self, request, query: str = None, *args, **kwargs):
        """Search movies"""
        finded_movies = tmdb_api.search_movies(query)
        serialized = serializers.ListTMDBMovieSerializer(data=finded_movies, many=True)
        serialized.is_valid(raise_exception=True)
        return Response(serialized.data, status=status.HTTP_200_OK)


class PlanToWatchViewSet(GenericViewSet, ListModelMixin, DestroyModelMixin):
    """Viewset for PlanToWatch model"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    serializer_class = serializers.ListPlanToWatchSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        actions = {
            "list": serializers.ListPlanToWatchSerializer,
            "create": serializers.CreatePlanToWatchSerializer,
        }
        return actions.get(self.action, serializers.DefaultSerializer)

    def get_queryset(self):
        return PlanToWatch.objects.filter(profile=self.request.user.profile)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = serializers.CreatePlanToWatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan_to_watch = services.create_plan_to_watch(**serializer.validated_data, profile=request.user.profile)
        return Response(serializers.ListPlanToWatchSerializer(plan_to_watch).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        id = kwargs.get("pk")
        plan = services.retrieve_plan_to_watch_by_movie_id(movie_id=id, profile=request.user.profile)
        serialized = serializers.ListPlanToWatchSerializer(plan)
        return Response(serialized.data)
