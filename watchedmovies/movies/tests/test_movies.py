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
    assert response.data["results"][0]["title"] == watched_movie.title
    assert response.data["results"][0]["original_title"] == watched_movie.original_title


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
