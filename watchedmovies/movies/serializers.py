from rest_framework import serializers

from watchedmovies.movies.models import ViewDetails, WatchedMovie


class WatchedMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedMovie
        fields = "__all__"


class ViewDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewDetails
        fields = "__all__"
