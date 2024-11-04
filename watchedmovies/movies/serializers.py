from django.db import models
from rest_framework import serializers

from watchedmovies.movies.models import ViewDetails, WatchedMovie
from watchedmovies.movies.utils import get_backdrop_path, get_poster_path


class DefaultSerializer(serializers.Serializer):
    """Default serializer to handle empty requests"""

    pass


class ListWatchedMovieSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    release_date = serializers.DateField()
    total_views = serializers.SerializerMethodField()
    vote_average = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()

    def get_total_views(self, obj):
        return ViewDetails.objects.filter(watched_movie=obj.id).count()

    def get_vote_average(self, obj):
        return ViewDetails.objects.filter(watched_movie=obj.id).aggregate(models.Avg("rating"))["rating__avg"]

    def get_poster_url(self, obj):
        if obj.poster_path == "" or obj.poster_path is None:
            return None

        return get_poster_path(obj.poster_path)

    class Meta:
        model = WatchedMovie
        fields = ["id", "title", "release_date", "total_views", "vote_average", "poster_url"]


class WatchedMovieSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    poster_url = serializers.SerializerMethodField()
    backdrop_url = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    def get_poster_url(self, obj):
        if obj.poster_path == "" or obj.poster_path is None:
            return None

        return get_poster_path(obj.poster_path)

    def get_backdrop_url(self, obj):
        if obj.backdrop_path == "" or obj.backdrop_path is None:
            return None

        return get_backdrop_path(obj.backdrop_path)

    def get_total_views(self, obj):
        profile = self.context.get("profile")
        return ViewDetails.objects.filter(watched_movie=obj.id, profile=profile).count()

    def get_average_rating(self, obj):
        profile = self.context.get("profile")
        ratings = ViewDetails.objects.filter(watched_movie=obj.id, profile=profile)
        return ratings.aggregate(models.Avg("rating"))["rating__avg"]

    class Meta:
        model = WatchedMovie
        fields = "__all__"


class ListTMDBMovieSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    adult = serializers.BooleanField(allow_null=True, required=False)
    backdrop_path = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    genre_ids = serializers.ListField(child=serializers.IntegerField(), allow_null=True, required=False)
    original_language = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    original_title = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    overview = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    popularity = serializers.DecimalField(max_digits=10, decimal_places=3, allow_null=True, required=False)
    poster_path = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    release_date = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    title = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    video = serializers.BooleanField(allow_null=True, required=False)
    vote_average = serializers.DecimalField(max_digits=5, decimal_places=3, allow_null=True, required=False)
    vote_count = serializers.IntegerField(allow_null=True, required=False)
    poster_url = serializers.SerializerMethodField()
    backdrop_url = serializers.SerializerMethodField()

    def get_poster_url(self, obj):
        if obj is None:
            return None

        if obj.get("poster_path") is None:
            return None

        return get_poster_path(obj.get("poster_path"))

    def get_backdrop_url(self, obj):
        if obj is None:
            return None

        if obj.get("backdrop_path") is None:
            return None

        return get_backdrop_path(obj.get("backdrop_path"))


class CreateViewDetailSerializer(serializers.ModelSerializer):
    watched_movie = WatchedMovieSerializer(required=True)
    rating = serializers.IntegerField(min_value=1, max_value=10, required=False)
    comment = serializers.CharField(required=False, allow_blank=True)
    watched_date = serializers.DateTimeField(format="%Y-%m-%d", required=False)

    class Meta:
        model = ViewDetails
        exclude = ["profile"]


class UpdateViewDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewDetails
        exclude = ["watched_movie", "profile"]


class ListViewDetailSerializer(serializers.ModelSerializer):
    language = serializers.CharField(source="get_language_display")
    place = serializers.CharField(source="get_place_display")
    watched_at = serializers.DateTimeField(format="%Y-%m")

    class Meta:
        model = ViewDetails
        exclude = ["profile", "watched_movie"]
