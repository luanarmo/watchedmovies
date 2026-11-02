import hashlib
from urllib.parse import quote

import requests
from django.core.cache import cache

from config.settings.base import env

BASE_URL = "https://api.themoviedb.org/3"
API_KEY = env("TMDB_API_KEY")

TMDB_REQUEST_TIMEOUT = 10  # seconds, so a stalled TMDB request can't hang the worker

# Only successful (200) responses are cached: caching a failure would keep serving it until the TTL expires.
MOVIE_DETAILS_TTL = 60 * 60 * 24  # movie data barely changes
POPULAR_MOVIES_TTL = 60 * 60
SEARCH_MOVIES_TTL = 60 * 10


def make_request(url):
    """Make a request to the TMDB API, adding the Authorization header."""
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    return requests.get(url, headers=headers, timeout=TMDB_REQUEST_TIMEOUT)


def _fetch_json(url, *, cache_key: str, ttl: int) -> None | dict:
    """Return the JSON of a TMDB endpoint, served from the cache when possible.

    Returns None when TMDB fails (non-200, timeout or network error); failures are never cached."""
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        response = make_request(url)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    cache.set(cache_key, data, ttl)
    return data


def get_movie_details(movie_id) -> None | dict:
    """Get the details of a movie by its ID."""
    url = f"{BASE_URL}/movie/{movie_id}?language=en-US"
    return _fetch_json(url, cache_key=f"tmdb:movie:{movie_id}", ttl=MOVIE_DETAILS_TTL)


def get_popular_movies():
    """Get a list of popular movies"""
    url = f"{BASE_URL}/movie/popular?language=en-US&page=1"
    data = _fetch_json(url, cache_key="tmdb:popular", ttl=POPULAR_MOVIES_TTL)
    return data if data is not None else {"results": []}


def search_movies(query, page=1):
    """Search movies by a query"""
    url = f"{BASE_URL}/search/movie?query={quote(str(query), safe='')}&page={page}"
    # Hash the normalized query: raw user input is not a safe cache key (length, spaces, control characters).
    query_hash = hashlib.md5(str(query).strip().lower().encode(), usedforsecurity=False).hexdigest()
    data = _fetch_json(url, cache_key=f"tmdb:search:{query_hash}:{page}", ttl=SEARCH_MOVIES_TTL)

    if data is None:
        return {"results": [], "total_pages": 1, "total_results": 0}

    return {
        "results": data["results"],
        "total_pages": data["total_pages"],
        "total_results": data["total_results"],
    }
