from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth.models import AnonymousUser

from watchedmovies.services import tmdb_api

from ..views import TMDBViewSet

FAKE_URL = "/fake/"
MAKE_REQUEST = "watchedmovies.services.tmdb_api.make_request"


def fake_response(payload=None, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


@patch(MAKE_REQUEST)
def test_movie_details_is_requested_once_and_then_cached(mock_request):
    mock_request.return_value = fake_response({"id": 1, "title": "Fake"})

    first = tmdb_api.get_movie_details(1)
    second = tmdb_api.get_movie_details(1)

    assert first == second == {"id": 1, "title": "Fake"}
    assert mock_request.call_count == 1


@patch(MAKE_REQUEST)
def test_movie_details_cache_is_per_movie(mock_request):
    mock_request.return_value = fake_response({"id": 1})

    tmdb_api.get_movie_details(1)
    tmdb_api.get_movie_details(2)

    assert mock_request.call_count == 2


@patch(MAKE_REQUEST)
def test_failed_responses_are_not_cached(mock_request):
    mock_request.return_value = fake_response(status_code=500)

    assert tmdb_api.get_movie_details(1) is None
    assert tmdb_api.get_movie_details(1) is None
    assert mock_request.call_count == 2

    mock_request.return_value = fake_response({"id": 1})
    assert tmdb_api.get_movie_details(1) == {"id": 1}


@patch(MAKE_REQUEST, side_effect=requests.Timeout)
def test_network_errors_return_none_and_are_not_cached(mock_request):
    assert tmdb_api.get_movie_details(1) is None
    assert tmdb_api.get_popular_movies() == {"results": []}
    assert tmdb_api.search_movies("matrix") == {"results": [], "total_pages": 1, "total_results": 0}


@patch(MAKE_REQUEST)
def test_popular_movies_is_cached(mock_request):
    mock_request.return_value = fake_response({"results": [{"id": 1}]})

    tmdb_api.get_popular_movies()
    assert tmdb_api.get_popular_movies() == {"results": [{"id": 1}]}
    assert mock_request.call_count == 1


@patch(MAKE_REQUEST)
def test_search_is_cached_per_normalized_query_and_page(mock_request):
    mock_request.return_value = fake_response({"results": [], "total_pages": 1, "total_results": 0})

    tmdb_api.search_movies("Matrix", 1)
    tmdb_api.search_movies(" matrix ", 1)  # same query once normalized
    assert mock_request.call_count == 1

    tmdb_api.search_movies("matrix", 2)  # another page
    tmdb_api.search_movies("alien", 1)  # another query
    assert mock_request.call_count == 3


@patch(MAKE_REQUEST)
def test_search_escapes_the_query(mock_request):
    mock_request.return_value = fake_response({"results": [], "total_pages": 1, "total_results": 0})

    tmdb_api.search_movies("a&page=9 b", 1)

    assert "query=a%26page%3D9%20b&page=1" in mock_request.call_args.args[0]


@patch(MAKE_REQUEST)
def test_popular_movies_view_sends_public_cache_headers(mock_request, db, api_rf):
    mock_request.return_value = fake_response({"results": []})

    request = api_rf.get(FAKE_URL)
    request.user = AnonymousUser()
    response = TMDBViewSet.as_view({"get": "popular_movies"})(request)

    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert f"max-age={tmdb_api.POPULAR_MOVIES_TTL}" in response["Cache-Control"]


@patch(MAKE_REQUEST)
def test_movie_details_view_returns_404_when_tmdb_has_no_data(mock_request, db, api_rf):
    mock_request.return_value = fake_response(status_code=404)

    request = api_rf.get(FAKE_URL)
    request.user = AnonymousUser()
    response = TMDBViewSet.as_view({"get": "movie_details"})(request, movie_id="999")

    assert response.status_code == 404
