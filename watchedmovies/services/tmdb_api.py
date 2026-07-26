import json

import requests

from config.settings.base import env

BASE_URL = "https://api.themoviedb.org/3"
API_KEY = env("TMDB_API_KEY")


def make_request(url):
    """Make a request to the TMDB API, adding the Authorization header."""
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    return requests.get(url, headers=headers)


def get_movie_details(movie_id) -> None | dict:
    """Get the details of a movie by its ID."""
    url = f"{BASE_URL}/movie/{movie_id}?language=en-US"
    response = make_request(url)

    if response.status_code != 200:
        return None

    return response.json()


def get_popular_movies():
    """Get a list of popular movies"""
    url = f"{BASE_URL}/movie/popular?language=en-US&page=1"
    response = make_request(url)

    if response.status_code != 200:
        return json.dumps([])

    return response.json()


def search_movies(query, page=1):
    """Search movies by a query"""
    url = f"{BASE_URL}/search/movie?query={query}&page={page}"
    response = make_request(url)

    if response.status_code != 200:
        return {"results": [], "total_pages": 1, "total_results": 0}

    data = response.json()
    return {
        "results": data["results"],
        "total_pages": data["total_pages"],
        "total_results": data["total_results"],
    }
