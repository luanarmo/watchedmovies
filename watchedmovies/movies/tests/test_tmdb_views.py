from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser

from watchedmovies.movies.models import PlanToWatch
from watchedmovies.users.tests.factories import ProfileFactory

from ..views import TMDBViewSet
from .factories import ViewDetailFactory, WatchedMovieFactory

FAKE_URL = "/fake/"

FAKE_TMDB_DATA = {
    "id": 0,
    "title": "Fake Movie",
    "genre_ids": [1],
    "poster_path": None,
    "backdrop_path": None,
}


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details")
def test_movie_details_flags_false_for_anonymous(mock_get, db, api_rf):
    mock_get.return_value = {**FAKE_TMDB_DATA, "id": 999}

    request = api_rf.get(FAKE_URL)
    request.user = AnonymousUser()
    response = TMDBViewSet.as_view({"get": "movie_details"})(request, movie_id="999")

    assert response.status_code == 200
    assert response.data["is_watched"] is False
    assert response.data["is_plan_to_watch"] is False


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details")
def test_movie_details_flags_false_when_authenticated_no_lists(mock_get, db, user, api_rf):
    ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    mock_get.return_value = {**FAKE_TMDB_DATA, "id": watched_movie.id}

    request = api_rf.get(FAKE_URL)
    request.user = user
    response = TMDBViewSet.as_view({"get": "movie_details"})(request, movie_id=str(watched_movie.id))

    assert response.status_code == 200
    assert response.data["is_watched"] is False
    assert response.data["is_plan_to_watch"] is False


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details")
def test_movie_details_is_watched_true(mock_get, db, user, api_rf):
    profile = ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    ViewDetailFactory(profile=profile, watched_movie=watched_movie)
    mock_get.return_value = {**FAKE_TMDB_DATA, "id": watched_movie.id}

    request = api_rf.get(FAKE_URL)
    request.user = user
    response = TMDBViewSet.as_view({"get": "movie_details"})(request, movie_id=str(watched_movie.id))

    assert response.status_code == 200
    assert response.data["is_watched"] is True
    assert response.data["is_plan_to_watch"] is False


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details")
def test_movie_details_is_plan_to_watch_true(mock_get, db, user, api_rf):
    profile = ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    PlanToWatch.objects.create(movie=watched_movie, profile=profile)
    mock_get.return_value = {**FAKE_TMDB_DATA, "id": watched_movie.id}

    request = api_rf.get(FAKE_URL)
    request.user = user
    response = TMDBViewSet.as_view({"get": "movie_details"})(request, movie_id=str(watched_movie.id))

    assert response.status_code == 200
    assert response.data["is_watched"] is False
    assert response.data["is_plan_to_watch"] is True


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details")
def test_movie_details_both_flags_true(mock_get, db, user, api_rf):
    profile = ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    ViewDetailFactory(profile=profile, watched_movie=watched_movie)
    PlanToWatch.objects.create(movie=watched_movie, profile=profile)
    mock_get.return_value = {**FAKE_TMDB_DATA, "id": watched_movie.id}

    request = api_rf.get(FAKE_URL)
    request.user = user
    response = TMDBViewSet.as_view({"get": "movie_details"})(request, movie_id=str(watched_movie.id))

    assert response.status_code == 200
    assert response.data["is_watched"] is True
    assert response.data["is_plan_to_watch"] is True
