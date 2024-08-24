from rest_framework import serializers

from watchedmovies.movies.models import ViewDetails, WatchedMovie


class DefaultSerializer(serializers.Serializer):
    """Default serializer to handle empty requests"""

    pass


class WatchedMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedMovie
        fields = "__all__"


class ListWatchedMovieSerializer(serializers.ModelSerializer):
    view_details = serializers.HyperlinkedIdentityField(view_name="view-details-detail", lookup_field="id")

    class Meta:
        model = WatchedMovie
        fields = ["id", "title", "release_date", "vote_average", "vote_count", "view_details"]


class CreateViewDetailSerializer(serializers.ModelSerializer):
    watched_movie = WatchedMovieSerializer(required=True)

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

    class Meta:
        model = ViewDetails
        exclude = ["profile", "watched_movie"]
