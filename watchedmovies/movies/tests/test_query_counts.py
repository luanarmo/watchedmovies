from django.db import connection
from django.test.utils import CaptureQueriesContext

from watchedmovies.users.tests.factories import ProfileFactory

from ..models import PlanToWatch
from ..views import PlanToWatchViewSet
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
