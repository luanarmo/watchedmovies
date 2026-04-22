from unittest.mock import patch

from watchedmovies.movies.services import get_or_create_watched_movie
from watchedmovies.users.tests.factories import ProfileFactory

from ..models import ViewDetails, WatchedMovie
from ..views import ViewDetailViewSet, WatchedMovieViewSet
from .factories import ViewDetailFactory, WatchedMovieFactory

FAKE = "/fake-url/"


def test_register_view_detail(db, user, api_rf):
    ProfileFactory(user=user)
    movie_data = {
        "id": 1,
        "adult": False,
        "backdrop_path": "/fake-backdrop-path/",
        "genre_ids": "[1, 2, 3]",
        "original_language": "en",
        "original_title": "Fake Original Title",
        "overview": "Fake overview",
        "popularity": 9.99,
        "poster_path": "/fake-poster-path/",
        "release_date": "2021-01-01",
        "title": "Fake Title",
        "video": False,
        "vote_average": 9.99,
        "vote_count": 100,
    }

    data = {
        "watched_movie": movie_data,
        "rating": 5,
        "comment": "Fake comment",
        "language": "en",
        "place": "home",
        "watched_date": "2024-11-05",
    }

    request = api_rf.post(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201
    assert response.data["rating"] == 5
    assert response.data["comment"] == "Fake comment"


def test_list_view_details(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    request = api_rf.get(FAKE)
    request.user = user
    response = ViewDetailViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["rating"] == view_detail.rating
    assert response.data["results"][0]["comment"] == view_detail.comment


def test_retrieve_view_detail(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    request = api_rf.get(FAKE)
    request.user = user
    response = ViewDetailViewSet.as_view({"get": "retrieve"})(request, pk=view_detail.id)

    assert response.status_code == 200
    assert response.data["rating"] == view_detail.rating
    assert response.data["comment"] == view_detail.comment


def test_update_view_detail(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    data = {"rating": 4, "comment": "Updated comment"}

    request = api_rf.patch(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=view_detail.id)

    assert response.status_code == 200
    assert response.data["rating"] == 4
    assert response.data["comment"] == "Updated comment"


def test_list_watched_movies(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    ViewDetailFactory(profile=profile, watched_movie=watched_movie)

    request = api_rf.get(FAKE)
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["count"] == 1


def test_list_watched_movies_filter_by_watched_date_year(db, user, api_rf):
    profile = ProfileFactory(user=user)

    first_watched_movie = WatchedMovieFactory()
    second_watched_movie = WatchedMovieFactory()
    third_watched_movie = WatchedMovieFactory()

    ViewDetailFactory(profile=profile, watched_movie=second_watched_movie, watched_date="2022-01-01")
    ViewDetailFactory(profile=profile, watched_movie=first_watched_movie, watched_date="2021-12-31")
    ViewDetailFactory(profile=profile, watched_movie=third_watched_movie, watched_date="2022-01-02")

    # -first_watched_date&watched_date_year=2025
    request = api_rf.get(FAKE, {"watched_date_year": 2022, "ordering": "-first_watched_date"})
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["count"] == 2


def test_retrieve_watched_movie(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    ViewDetailFactory(profile=profile, watched_movie=watched_movie)

    request = api_rf.get(FAKE)
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "retrieve"})(request, pk=watched_movie.id)

    assert response.status_code == 200
    assert response.data["title"] == watched_movie.title
    assert response.data["original_title"] == watched_movie.original_title


def test_destroy_watched_movie(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    ViewDetailFactory(profile=profile, watched_movie=watched_movie)

    request = api_rf.delete(FAKE)
    request.user = user
    response = WatchedMovieViewSet.as_view({"delete": "destroy"})(request, pk=watched_movie.id)

    assert response.status_code == 204
    assert WatchedMovie.objects.filter(id=watched_movie.id).exists()
    assert not ViewDetails.objects.filter(watched_movie=watched_movie).exists()


def test_get_or_create_watched_movie(db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie_data = {
        "id": 1,
        "adult": False,
        "backdrop_path": "/fake-backdrop-path/",
        "genre_ids": "[1, 2, 3]",
        "original_language": "en",
        "original_title": "Fake Original Title",
        "overview": "Fake overview",
        "popularity": 9.99,
        "poster_path": "/fake-poster-path/",
        "release_date": "2021-01-01",
        "title": "Fake Title",
        "video": False,
        "vote_average": 9.99,
        "vote_count": 100,
    }

    data = {
        "watched_movie": movie_data,
        "rating": 5,
        "comment": "Fake comment",
        "language": "en",
        "place": "home",
        "watched_date": "2024-11-05",
    }

    request = api_rf.post(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201
    profile.refresh_from_db()
    assert WatchedMovie.objects.count() == 1

    request = api_rf.post(FAKE, data, format="json")
    request.user = user

    response = ViewDetailViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201

    assert WatchedMovie.objects.count() == 1


BASE_MOVIE_DATA = {
    "id": 99,
    "adult": False,
    "backdrop_path": "/fake/",
    "genre_ids": "[1]",
    "original_language": "en",
    "original_title": "Original Title",
    "overview": "overview",
    "popularity": 7.5,
    "poster_path": "/fake/",
    "release_date": "2022-06-15",
    "title": "Title",
    "video": False,
    "vote_average": 8.0,
    "vote_count": 200,
}


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details", return_value=None)
def test_get_or_create_finds_by_original_title_and_release_date(mock_details, db):
    movie = get_or_create_watched_movie(watched_movie=BASE_MOVIE_DATA)
    found = get_or_create_watched_movie(watched_movie=BASE_MOVIE_DATA)

    assert WatchedMovie.objects.count() == 1
    assert found.id == movie.id


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details", return_value=None)
def test_get_or_create_finds_by_title_when_original_title_is_none(mock_details, db):
    movie = get_or_create_watched_movie(watched_movie=BASE_MOVIE_DATA)
    data_without_original = {**BASE_MOVIE_DATA, "original_title": None}
    found = get_or_create_watched_movie(watched_movie=data_without_original)

    assert WatchedMovie.objects.count() == 1
    assert found.id == movie.id


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details", return_value=None)
def test_get_or_create_creates_new_when_no_match(mock_details, db):
    different_data = {**BASE_MOVIE_DATA, "original_title": "Different", "title": "Different Title", "id": 100}
    get_or_create_watched_movie(watched_movie=BASE_MOVIE_DATA)
    get_or_create_watched_movie(watched_movie=different_data)

    assert WatchedMovie.objects.count() == 2


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details", return_value=None)
def test_get_or_create_no_duplicate_when_second_call_has_only_title(mock_details, db):
    get_or_create_watched_movie(watched_movie=BASE_MOVIE_DATA)
    data_title_only = {**BASE_MOVIE_DATA, "original_title": None}
    found = get_or_create_watched_movie(watched_movie=data_title_only)

    assert WatchedMovie.objects.count() == 1
    assert found.title == BASE_MOVIE_DATA["title"]
