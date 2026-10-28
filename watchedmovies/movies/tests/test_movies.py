from unittest.mock import patch

import pytest

from watchedmovies.movies.services import get_or_create_watched_movie
from watchedmovies.users.tests.factories import ProfileFactory

from ..models import MovieTier, ViewDetails, WatchedMovie
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


def test_register_view_detail_saves_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie_data = {
        "id": 1,
        "original_language": "en",
        "original_title": "Fake Original Title",
        "popularity": 9.99,
        "release_date": "2021-01-01",
        "title": "Fake Title",
        "vote_average": 9.99,
        "vote_count": 100,
    }

    data = {"watched_movie": movie_data, "watched_date": "2024-11-05", "tier": 5}

    request = api_rf.post(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201
    assert MovieTier.objects.get(profile=profile, movie_id=1).tier == 5


# One request per test: DRF marks the test transaction for rollback on a 4xx under ATOMIC_REQUESTS.
@pytest.mark.parametrize("tier", [0, 6])
def test_register_view_detail_rejects_out_of_range_tier(db, user, api_rf, tier):
    ProfileFactory(user=user)
    movie_data = {
        "id": 1,
        "original_language": "en",
        "original_title": "Fake Original Title",
        "popularity": 9.99,
        "release_date": "2021-01-01",
        "title": "Fake Title",
        "vote_average": 9.99,
        "vote_count": 100,
    }

    data = {"watched_movie": movie_data, "watched_date": "2024-11-05", "tier": tier}

    request = api_rf.post(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 400


def test_register_view_detail_with_null_tier_clears_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie = WatchedMovieFactory(original_title="Fake Original Title", title="Fake Title", release_date="2021-01-01")
    MovieTier.objects.create(profile=profile, movie=movie, tier=5)
    movie_data = {
        "id": movie.id,
        "original_language": "en",
        "original_title": "Fake Original Title",
        "popularity": 9.99,
        "release_date": "2021-01-01",
        "title": "Fake Title",
        "vote_average": 9.99,
        "vote_count": 100,
    }

    data = {"watched_movie": movie_data, "watched_date": "2024-11-05", "tier": None}

    request = api_rf.post(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201
    assert not MovieTier.objects.filter(profile=profile, movie=movie).exists()


def test_register_view_detail_without_tier_keeps_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie = WatchedMovieFactory(original_title="Fake Original Title", title="Fake Title", release_date="2021-01-01")
    MovieTier.objects.create(profile=profile, movie=movie, tier=5)
    movie_data = {
        "id": movie.id,
        "original_language": "en",
        "original_title": "Fake Original Title",
        "popularity": 9.99,
        "release_date": "2021-01-01",
        "title": "Fake Title",
        "vote_average": 9.99,
        "vote_count": 100,
    }

    data = {"watched_movie": movie_data, "watched_date": "2024-11-05"}

    request = api_rf.post(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201
    assert MovieTier.objects.get(profile=profile, movie=movie).tier == 5


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


def test_update_view_detail_saves_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    request = api_rf.patch(FAKE, {"tier": 3}, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=view_detail.id)

    assert response.status_code == 200
    assert MovieTier.objects.get(profile=profile, movie=view_detail.watched_movie).tier == 3


def test_update_view_detail_changes_tier_for_the_movie_not_the_view(db, user, api_rf):
    profile = ProfileFactory(user=user)
    first_view = ViewDetailFactory(profile=profile)
    second_view = ViewDetailFactory(profile=profile, watched_movie=first_view.watched_movie)
    MovieTier.objects.create(profile=profile, movie=first_view.watched_movie, tier=5)

    request = api_rf.patch(FAKE, {"tier": 2}, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=second_view.id)

    assert response.status_code == 200
    tiers = MovieTier.objects.filter(profile=profile, movie=first_view.watched_movie)
    assert [tier.tier for tier in tiers] == [2]


def test_update_view_detail_without_tier_keeps_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)
    MovieTier.objects.create(profile=profile, movie=view_detail.watched_movie, tier=4)

    request = api_rf.patch(FAKE, {"comment": "Only the comment"}, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=view_detail.id)

    assert response.status_code == 200
    assert MovieTier.objects.get(profile=profile, movie=view_detail.watched_movie).tier == 4


def test_update_view_detail_with_null_tier_clears_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)
    MovieTier.objects.create(profile=profile, movie=view_detail.watched_movie, tier=4)

    request = api_rf.patch(FAKE, {"tier": None}, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=view_detail.id)

    assert response.status_code == 200
    assert not MovieTier.objects.filter(profile=profile, movie=view_detail.watched_movie).exists()


def test_update_view_detail_returns_labels_and_codes(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    data = {"language": "es", "place": "cinema"}

    request = api_rf.patch(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=view_detail.id)

    assert response.status_code == 200
    assert response.data["language"] == "Spanish"
    assert response.data["language_code"] == "es"
    assert response.data["place"] == "Movie Theater"
    assert response.data["place_code"] == "cinema"


# One request per test: DRF marks the test transaction for rollback on a 4xx under ATOMIC_REQUESTS.
@pytest.mark.parametrize("rating", [0, 11])
def test_update_view_detail_rejects_out_of_range_rating(db, user, api_rf, rating):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    request = api_rf.patch(FAKE, {"rating": rating}, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=view_detail.id)

    assert response.status_code == 400


@pytest.mark.parametrize("tier", [0, 6])
def test_update_view_detail_rejects_out_of_range_tier(db, user, api_rf, tier):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    request = api_rf.patch(FAKE, {"tier": tier}, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=view_detail.id)

    assert response.status_code == 400


def test_update_view_detail_clears_rating(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile, rating=5)

    request = api_rf.patch(FAKE, {"rating": None}, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=view_detail.id)

    assert response.status_code == 200
    assert response.data["rating"] is None
    view_detail.refresh_from_db()
    assert view_detail.rating is None


def test_update_view_detail_of_other_profile_returns_404(db, user, api_rf):
    ProfileFactory(user=user)
    other_view_detail = ViewDetailFactory(profile=ProfileFactory())

    request = api_rf.patch(FAKE, {"rating": 3}, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"patch": "partial_update"})(request, pk=other_view_detail.id)

    assert response.status_code == 404


def test_full_update_view_detail(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    data = {
        "rating": 7,
        "comment": "Full update",
        "language": "fr",
        "place": "home",
        "watched_date": "2025-03-10",
        "is_favorite": True,
    }

    request = api_rf.put(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"put": "update"})(request, pk=view_detail.id)

    assert response.status_code == 200
    assert response.data["rating"] == 7
    assert response.data["watched_date"] == "2025-03-10"
    assert response.data["is_favorite"] is True


def test_list_view_details_includes_codes(db, user, api_rf):
    profile = ProfileFactory(user=user)
    view_detail = ViewDetailFactory(profile=profile)

    request = api_rf.get(FAKE)
    request.user = user
    response = ViewDetailViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["results"][0]["language_code"] == view_detail.language
    assert response.data["results"][0]["place_code"] == view_detail.place


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


def test_retrieve_watched_movie_includes_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    ViewDetailFactory(profile=profile, watched_movie=watched_movie)
    MovieTier.objects.create(profile=profile, movie=watched_movie, tier=4)

    request = api_rf.get(FAKE)
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "retrieve"})(request, pk=watched_movie.id)

    assert response.status_code == 200
    assert response.data["tier"] == 4


def test_retrieve_watched_movie_ignores_other_profile_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watched_movie = WatchedMovieFactory()
    ViewDetailFactory(profile=profile, watched_movie=watched_movie)
    MovieTier.objects.create(profile=ProfileFactory(), movie=watched_movie, tier=5)

    request = api_rf.get(FAKE)
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "retrieve"})(request, pk=watched_movie.id)

    assert response.status_code == 200
    assert response.data["tier"] is None


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


def test_watched_movie_total_views_after_watching_twice(db, user, api_rf):
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

    for _ in range(2):
        request = api_rf.post(FAKE, data, format="json")
        request.user = user
        response = ViewDetailViewSet.as_view({"post": "create"})(request)
        assert response.status_code == 201

    assert WatchedMovie.objects.count() == 1
    assert ViewDetails.objects.count() == 2

    watched_movie = WatchedMovie.objects.get()

    request = api_rf.get(FAKE)
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "retrieve"})(request, pk=watched_movie.id)

    assert response.status_code == 200
    assert response.data["total_views"] == 2


def test_list_watched_movies_filter_by_year_counts_only_that_year_views(db, user, api_rf):
    profile = ProfileFactory(user=user)
    other_profile = ProfileFactory()
    watched_movie = WatchedMovieFactory()

    # objects.create: ViewDetailFactory uses get_or_create on (watched_movie, profile),
    # so it can't create several views of the same movie for the same profile.
    ViewDetails.objects.create(profile=profile, watched_movie=watched_movie, watched_date="2026-04-01")
    ViewDetails.objects.create(profile=profile, watched_movie=watched_movie, watched_date="2026-09-25")
    ViewDetails.objects.create(profile=profile, watched_movie=watched_movie, watched_date="2025-01-10")
    ViewDetails.objects.create(profile=other_profile, watched_movie=watched_movie, watched_date="2026-05-05")

    request = api_rf.get(FAKE, {"watched_date_year": 2026, "ordering": "-first_watched_date"})
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == watched_movie.id
    assert response.data["results"][0]["total_views"] == 2


def test_list_watched_movies_filter_by_year_averages_only_that_year_ratings(db, user, api_rf):
    profile = ProfileFactory(user=user)
    other_profile = ProfileFactory()
    watched_movie = WatchedMovieFactory()

    ViewDetails.objects.create(profile=profile, watched_movie=watched_movie, watched_date="2026-04-01", rating=4)
    ViewDetails.objects.create(profile=profile, watched_movie=watched_movie, watched_date="2026-09-25", rating=2)
    ViewDetails.objects.create(profile=profile, watched_movie=watched_movie, watched_date="2025-01-10", rating=5)
    ViewDetails.objects.create(profile=other_profile, watched_movie=watched_movie, watched_date="2026-05-05", rating=1)

    request = api_rf.get(FAKE, {"watched_date_year": 2026})
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["results"][0]["vote_average"] == 3.0


def test_list_watched_movies_filter_by_year_is_favorite_only_from_that_year(db, user, api_rf):
    profile = ProfileFactory(user=user)
    other_profile = ProfileFactory()
    favorite_other_year = WatchedMovieFactory()
    favorite_this_year = WatchedMovieFactory()

    ViewDetails.objects.create(profile=profile, watched_movie=favorite_other_year, watched_date="2026-03-01")
    ViewDetails.objects.create(
        profile=profile, watched_movie=favorite_other_year, watched_date="2025-03-01", is_favorite=True
    )
    ViewDetails.objects.create(
        profile=other_profile, watched_movie=favorite_other_year, watched_date="2026-03-01", is_favorite=True
    )
    ViewDetails.objects.create(
        profile=profile, watched_movie=favorite_this_year, watched_date="2026-06-01", is_favorite=True
    )

    request = api_rf.get(FAKE, {"watched_date_year": 2026})
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    is_favorite_by_id = {movie["id"]: movie["is_favorite"] for movie in response.data["results"]}
    assert is_favorite_by_id == {favorite_other_year.id: False, favorite_this_year.id: True}


def test_list_watched_movies_filter_by_year_orders_by_that_year_last_view(db, user, api_rf):
    profile = ProfileFactory(user=user)
    other_profile = ProfileFactory()
    rewatched_next_year = WatchedMovieFactory()
    watched_mid_year = WatchedMovieFactory()

    ViewDetails.objects.create(profile=profile, watched_movie=rewatched_next_year, watched_date="2026-02-01")
    ViewDetails.objects.create(profile=profile, watched_movie=rewatched_next_year, watched_date="2027-01-15")
    ViewDetails.objects.create(profile=other_profile, watched_movie=rewatched_next_year, watched_date="2026-12-31")
    ViewDetails.objects.create(profile=profile, watched_movie=watched_mid_year, watched_date="2026-06-01")

    request = api_rf.get(FAKE, {"watched_date_year": 2026, "ordering": "-first_watched_date"})
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert [movie["id"] for movie in response.data["results"]] == [watched_mid_year.id, rewatched_next_year.id]


def test_list_watched_movies_without_year_aggregates_all_years_for_own_profile(db, user, api_rf):
    profile = ProfileFactory(user=user)
    other_profile = ProfileFactory()
    watched_movie = WatchedMovieFactory()

    ViewDetails.objects.create(profile=profile, watched_movie=watched_movie, watched_date="2026-04-01", rating=4)
    ViewDetails.objects.create(profile=profile, watched_movie=watched_movie, watched_date="2025-01-10", rating=2)
    ViewDetails.objects.create(
        profile=other_profile, watched_movie=watched_movie, watched_date="2026-05-05", rating=1, is_favorite=True
    )

    request = api_rf.get(FAKE)
    request.user = user
    response = WatchedMovieViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["count"] == 1
    movie = response.data["results"][0]
    assert movie["total_views"] == 2
    assert movie["vote_average"] == 3.0
    assert movie["is_favorite"] is False


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
def test_register_view_detail_when_tmdb_changed_release_date(mock_details, db, user, api_rf):
    profile = ProfileFactory(user=user)
    get_or_create_watched_movie(watched_movie=BASE_MOVIE_DATA)
    data = {
        "watched_movie": {**BASE_MOVIE_DATA, "release_date": "2022-06-16"},
        "watched_date": "2024-11-05",
    }

    request = api_rf.post(FAKE, data, format="json")
    request.user = user
    response = ViewDetailViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201
    assert WatchedMovie.objects.count() == 1
    assert ViewDetails.objects.filter(profile=profile, watched_movie_id=BASE_MOVIE_DATA["id"]).exists()


@patch("watchedmovies.movies.services.tmdb_api.get_movie_details", return_value=None)
def test_get_or_create_no_duplicate_when_second_call_has_only_title(mock_details, db):
    get_or_create_watched_movie(watched_movie=BASE_MOVIE_DATA)
    data_title_only = {**BASE_MOVIE_DATA, "original_title": None}
    found = get_or_create_watched_movie(watched_movie=data_title_only)

    assert WatchedMovie.objects.count() == 1
    assert found.title == BASE_MOVIE_DATA["title"]
