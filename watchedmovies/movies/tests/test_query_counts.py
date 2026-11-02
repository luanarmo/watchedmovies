import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from watchedmovies.users.tests.factories import ProfileFactory

from ..models import MovieTier, PlanToWatch, ViewDetails
from ..views import PlanToWatchViewSet, WatchedMovieViewSet
from .factories import WatchedMovieFactory

FAKE = "/fake-url/"


def list_plan_to_watch(user, api_rf):
    request = api_rf.get(FAKE)
    request.user = user
    return PlanToWatchViewSet.as_view({"get": "list"})(request)


def add_plans(profile, amount):
    for _ in range(amount):
        PlanToWatch.objects.create(movie=WatchedMovieFactory(), profile=profile)


def count_list_queries(user, api_rf):
    with CaptureQueriesContext(connection) as queries:
        response = list_plan_to_watch(user, api_rf)
    assert response.status_code == 200
    return len(queries), len(response.data["results"])


def test_plan_to_watch_list_query_count_does_not_grow_with_items(db, user, api_rf):
    profile = ProfileFactory(user=user)

    add_plans(profile, 2)
    few_queries, few_items = count_list_queries(user, api_rf)

    add_plans(profile, 4)
    many_queries, many_items = count_list_queries(user, api_rf)

    assert (few_items, many_items) == (2, 6)
    assert many_queries == few_queries, f"N+1: {few_queries} queries for 2 plans, {many_queries} for 6"


def list_watched_movies(user, api_rf, params):
    request = api_rf.get(FAKE, params)
    request.user = user
    return WatchedMovieViewSet.as_view({"get": "list"})(request)


def add_watched_movies(profile, amount):
    """Each movie gets two views, one of them favorite, and a tier: every annotation of the list is exercised."""
    for _ in range(amount):
        movie = WatchedMovieFactory()
        ViewDetails.objects.create(profile=profile, watched_movie=movie, watched_date="2026-04-01", is_favorite=True)
        ViewDetails.objects.create(profile=profile, watched_movie=movie, watched_date="2026-09-25")
        MovieTier.objects.create(profile=profile, movie=movie, tier=4)


def count_watched_movies_list_queries(user, api_rf, params):
    with CaptureQueriesContext(connection) as queries:
        response = list_watched_movies(user, api_rf, params)
    assert response.status_code == 200
    return len(queries), len(response.data["results"])


@pytest.mark.parametrize("params", [{}, {"watched_date_year": 2026}], ids=["all-years", "filtered-by-year"])
def test_watched_movies_list_query_count_does_not_grow_with_items(db, user, api_rf, params):
    profile = ProfileFactory(user=user)

    add_watched_movies(profile, 2)
    few_queries, few_items = count_watched_movies_list_queries(user, api_rf, params)

    add_watched_movies(profile, 4)
    many_queries, many_items = count_watched_movies_list_queries(user, api_rf, params)

    assert (few_items, many_items) == (2, 6)
    assert many_queries == few_queries, f"N+1: {few_queries} queries for 2 movies, {many_queries} for 6"
