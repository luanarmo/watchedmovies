from unittest.mock import MagicMock, patch

from watchedmovies.movies.serializers import WatchedMovieSerializer
from watchedmovies.movies.utils import extract_directors
from watchedmovies.services import tmdb_api

from .factories import WatchedMovieFactory

MAKE_REQUEST = "watchedmovies.services.tmdb_api.make_request"

CREDITS = {
    "cast": [{"name": "Some Actor", "job": None}],
    "crew": [
        {"name": "Some Writer", "job": "Screenplay"},
        {"name": "Lana Wachowski", "job": "Director"},
        {"name": "Lilly Wachowski", "job": "Director"},
    ],
}


def test_extract_directors_returns_only_the_crew_with_the_director_job():
    assert extract_directors({"credits": CREDITS}) == ["Lana Wachowski", "Lilly Wachowski"]


def test_extract_directors_is_empty_when_there_are_no_credits():
    assert extract_directors(None) == []
    assert extract_directors({}) == []
    assert extract_directors({"credits": None}) == []
    assert extract_directors({"credits": {"cast": []}}) == []
    assert extract_directors({"credits": {"crew": [{"name": "Writer", "job": "Screenplay"}]}}) == []


def test_extract_directors_ignores_nameless_entries():
    assert extract_directors({"credits": {"crew": [{"job": "Director"}, {"name": "", "job": "Director"}]}}) == []


def test_watched_movie_serializer_exposes_the_directors(db):
    movie = WatchedMovieFactory(more_details={"credits": CREDITS})

    assert WatchedMovieSerializer(movie).data["directors"] == ["Lana Wachowski", "Lilly Wachowski"]


def test_watched_movie_serializer_returns_no_directors_for_movies_without_credits(db):
    """Movies stored before credits were requested have no `credits` until the backfill command runs."""
    assert WatchedMovieSerializer(WatchedMovieFactory(more_details=None)).data["directors"] == []
    assert WatchedMovieSerializer(WatchedMovieFactory(more_details={"runtime": 100})).data["directors"] == []


@patch(MAKE_REQUEST)
def test_movie_details_requests_the_credits(mock_request):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"id": 4242, "credits": CREDITS}
    mock_request.return_value = response

    tmdb_api.get_movie_details(4242)

    assert "append_to_response=credits" in mock_request.call_args.args[0]
