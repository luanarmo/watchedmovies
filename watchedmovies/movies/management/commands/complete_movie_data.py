from django.core.management.base import BaseCommand

from watchedmovies.movies.models import WatchedMovie
from watchedmovies.movies.services import tmdb_api


class Command(BaseCommand):
    """
    This command completes the data of the movies. It makes a request to the TMDB API to get the details of each movie.
    """

    help = """This command completes the data of the movies. It makes
    a request to the TMDB API to get the details of each movie."""

    def handle(self, *args, **kwargs):
        watched_movies = WatchedMovie.objects.all()

        for watched_movie in watched_movies:
            movie_details = tmdb_api.get_movie_details(watched_movie.pk)
            watched_movie.runtime = movie_details.get("runtime")
            watched_movie.more_details = movie_details
            watched_movie.full_clean()
            watched_movie.save()

        self.stdout.write(
            self.style.SUCCESS("All movies have been updated successfully!"),
        )
