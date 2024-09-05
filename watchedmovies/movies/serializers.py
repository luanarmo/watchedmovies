from rest_framework import serializers

from watchedmovies.movies.models import ViewDetails, WatchedMovie


class DefaultSerializer(serializers.Serializer):
    """Default serializer to handle empty requests"""

    pass


class WatchedMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedMovie
        fields = "__all__"


class ListTMDBMovieSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    adult = serializers.BooleanField(allow_null=True, required=False)
    backdrop_path = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    genre_ids = serializers.ListField(child=serializers.IntegerField())
    original_language = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    original_title = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    overview = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    popularity = serializers.DecimalField(max_digits=10, decimal_places=3, allow_null=True, required=False)
    poster_path = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    release_date = serializers.SerializerMethodField()
    title = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    video = serializers.BooleanField(allow_null=True, required=False)
    vote_average = serializers.DecimalField(max_digits=5, decimal_places=3, allow_null=True, required=False)
    vote_count = serializers.IntegerField(allow_null=True, required=False)

    def get_release_date(self, obj):
        release_date = obj.get("release_date")
        if release_date == "":
            return None


class ListWatchedMovieSerializer(serializers.ModelSerializer):
    view_details = serializers.HyperlinkedIdentityField(view_name="view-details-detail", lookup_field="id")

    class Meta:
        model = WatchedMovie
        fields = ["id", "name", "release_date", "vote_average", "vote_count", "view_details"]


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
