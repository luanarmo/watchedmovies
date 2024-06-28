from rest_framework import serializers

from watchedmovies.movies.models import WatchedMovie


class WatchedMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedMovie
        exclude = ("profile",)
