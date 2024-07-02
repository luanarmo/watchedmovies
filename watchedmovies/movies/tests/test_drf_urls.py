from django.urls import resolve, reverse

from watchedmovies.movies.models import WatchedMovie


def test_movie_list():
    assert reverse("movies:watched-movies-list") == "/api/watched-movies/"
    assert resolve("/api/watched-movies/").view_name == "movies:watched-movies-list"


def test_movie_detail(watchedmovie: WatchedMovie):
    assert (
        reverse("movies:watched-movies-detail", kwargs={"pk": watchedmovie.pk})
        == f"/api/watched-movies/{watchedmovie.pk}/"
    )
    assert resolve(f"/api/watched-movies/{watchedmovie.pk}/").view_name == "movies:watched-movies-detail"
