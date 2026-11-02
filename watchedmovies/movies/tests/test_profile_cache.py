from datetime import date
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from watchedmovies.users.tests.factories import ProfileFactory

from .. import profile_cache, services
from ..models import MovieTier, ViewDetails
from ..views import ViewDetailViewSet, WatchedMovieViewSet
from .factories import WatchedMovieFactory

FAKE = "/fake-url/"
THIS_YEAR = date.today().year


@pytest.fixture
def profile(db):
    return ProfileFactory()


def watch(profile, movie=None, watched_date=date(2026, 3, 1)):
    return ViewDetails.objects.create(
        profile=profile, watched_movie=movie or WatchedMovieFactory(), watched_date=watched_date
    )


def query_count(func, *args, **kwargs):
    with CaptureQueriesContext(connection) as queries:
        result = func(*args, **kwargs)
    return result, len(queries)


# --- profile_cache ----------------------------------------------------------------------------------------------


def test_get_or_build_builds_once(db):
    calls = []

    def build():
        calls.append(1)
        return {"value": 1}

    assert profile_cache.get_or_build(1, "x", build=build) == {"value": 1}
    assert profile_cache.get_or_build(1, "x", build=build) == {"value": 1}
    assert len(calls) == 1


def test_get_or_build_separates_params_names_and_profiles():
    assert profile_cache.get_or_build(1, "x", 2025, build=lambda: "a") == "a"
    assert profile_cache.get_or_build(1, "x", 2026, build=lambda: "b") == "b"
    assert profile_cache.get_or_build(1, "y", 2025, build=lambda: "c") == "c"
    assert profile_cache.get_or_build(2, "x", 2025, build=lambda: "d") == "d"
    assert profile_cache.get_or_build(1, "x", 2025, build=lambda: "never") == "a"


def test_empty_values_are_cached_too():
    profile_cache.get_or_build(1, "x", build=list)
    assert profile_cache.get_or_build(1, "x", build=lambda: ["built again"]) == []


def test_invalidate_profile_only_affects_that_profile(db):
    profile_cache.get_or_build(1, "x", build=lambda: "old")
    profile_cache.get_or_build(2, "x", build=lambda: "old")

    profile_cache.invalidate_profile(1)

    assert profile_cache.get_or_build(1, "x", build=lambda: "new") == "new"
    assert profile_cache.get_or_build(2, "x", build=lambda: "new") == "old"


def test_result_built_before_an_invalidation_is_not_served_after_it(db):
    """A reader that started before a write must not leave stale data visible once the write invalidated."""

    def build_while_a_write_happens():
        profile_cache.invalidate_profile(1)
        return "stale"

    profile_cache.get_or_build(1, "x", build=build_while_a_write_happens)

    assert profile_cache.get_or_build(1, "x", build=lambda: "fresh") == "fresh"


# --- services are cached ----------------------------------------------------------------------------------------


def test_stats_are_served_from_the_cache(profile):
    watch(profile)

    first, first_queries = query_count(services.get_stats, profile=profile)
    second, second_queries = query_count(services.get_stats, profile=profile)

    assert first == second
    assert first_queries > 0
    assert second_queries == 0


def test_stats_cache_is_per_year(profile):
    watch(profile, watched_date=date(2025, 1, 1))
    watch(profile, watched_date=date(2026, 1, 1))
    watch(profile, watched_date=date(2026, 2, 1))

    assert services.get_stats(profile=profile, year="2025")["total_watched"] == 1
    assert services.get_stats(profile=profile, year="2026")["total_watched"] == 2
    assert services.get_stats(profile=profile)["total_watched"] == 3


def test_stats_cache_is_per_profile(profile):
    other = ProfileFactory()
    watch(profile)

    assert services.get_stats(profile=profile)["total_watched"] == 1
    assert services.get_stats(profile=other)["total_watched"] == 0


def test_years_are_served_from_the_cache(profile):
    watch(profile)

    _, first_queries = query_count(services.get_watched_register_years, profile=profile)
    years, second_queries = query_count(services.get_watched_register_years, profile=profile)

    assert years == {"years": [2026]}
    assert first_queries > 0
    assert second_queries == 0


@patch("watchedmovies.movies.services._build_wrapped", return_value=b"png")
def test_wrapped_is_built_once_per_year(mock_build, profile):
    services.create_wrapped(profile=profile, year="2025")
    services.create_wrapped(profile=profile, year="2025")
    assert mock_build.call_count == 1

    services.create_wrapped(profile=profile, year="2024")
    assert mock_build.call_count == 2


@patch("watchedmovies.movies.services._build_wrapped", return_value=b"png")
def test_wrapped_without_year_shares_the_entry_of_the_current_year(mock_build, profile):
    services.create_wrapped(profile=profile, year=None)
    services.create_wrapped(profile=profile, year=str(THIS_YEAR))

    assert mock_build.call_count == 1


@patch("watchedmovies.movies.services._build_tier_list_image", return_value="base64")
def test_tier_list_image_is_built_once_per_year(mock_build, profile):
    services.create_tier_list_image(profile=profile, year=2026)
    services.create_tier_list_image(profile=profile, year=2026)
    services.create_tier_list_image(profile=profile, year=None)
    services.create_tier_list_image(profile=profile, year=None)

    assert mock_build.call_count == 2


def test_tier_list_view_is_served_from_the_cache(profile, api_rf):
    movie = WatchedMovieFactory(title="Cached movie")
    watch(profile, movie, date(THIS_YEAR, 1, 1))
    MovieTier.objects.create(profile=profile, movie=movie, tier=5)

    def get_tier_list():
        request = api_rf.get(FAKE)
        request.user = profile.user
        return WatchedMovieViewSet.as_view({"get": "tier_list"})(request)

    first, _ = query_count(get_tier_list)
    second, second_queries = query_count(get_tier_list)

    assert first.status_code == second.status_code == 200
    assert [m["title"] for m in second.data] == ["Cached movie"]
    assert second_queries == 0


# --- invalidation -----------------------------------------------------------------------------------------------


def test_creating_a_view_invalidates_stats_and_years(profile):
    watch(profile)
    assert services.get_stats(profile=profile)["total_watched"] == 1
    assert services.get_watched_register_years(profile=profile) == {"years": [2026]}

    watch(profile, watched_date=date(2025, 5, 5))

    assert services.get_stats(profile=profile)["total_watched"] == 2
    assert services.get_watched_register_years(profile=profile) == {"years": [2026, 2025]}


def test_updating_a_view_invalidates_stats(profile):
    view = watch(profile, watched_date=date(2026, 1, 1))
    assert services.get_stats(profile=profile, year="2026")["total_watched"] == 1

    services.update_view_detail(view_detail=view, watched_date=date(2025, 1, 1))

    assert services.get_stats(profile=profile, year="2026")["total_watched"] == 0


def test_deleting_a_view_through_the_viewset_invalidates_stats(profile, api_rf):
    """ViewDetailViewSet.destroy calls view.delete() and skips the services: only a signal can see it."""
    view = watch(profile)
    assert services.get_stats(profile=profile)["total_watched"] == 1

    request = api_rf.delete(FAKE)
    request.user = profile.user
    response = ViewDetailViewSet.as_view({"delete": "destroy"})(request, pk=view.pk)

    assert response.status_code == 204
    assert services.get_stats(profile=profile)["total_watched"] == 0


def test_deleting_views_with_a_queryset_invalidates_stats(profile):
    watch(profile)
    assert services.get_stats(profile=profile)["total_watched"] == 1

    ViewDetails.objects.filter(profile=profile).delete()

    assert services.get_stats(profile=profile)["total_watched"] == 0


def test_changing_a_tier_invalidates_the_tier_list(profile, api_rf):
    movie = WatchedMovieFactory()
    watch(profile, movie, date(THIS_YEAR, 1, 1))

    def tier_list():
        request = api_rf.get(FAKE)
        request.user = profile.user
        return WatchedMovieViewSet.as_view({"get": "tier_list"})(request).data

    assert tier_list() == []

    services.set_movie_tier(movie=movie, profile=profile, tier=4)
    assert [m["tier"] for m in tier_list()] == [4]

    services.set_movie_tier(movie=movie, profile=profile, tier=None)
    assert tier_list() == []


def test_changing_a_movie_invalidates_the_stats_of_the_profiles_that_watched_it(profile):
    other = ProfileFactory()
    movie = WatchedMovieFactory(runtime=100)
    watch(profile, movie)
    assert services.get_stats(profile=profile)["total_runtime_minutes"] == 100
    services.get_stats(profile=other)

    movie.runtime = 200
    movie.save()

    assert services.get_stats(profile=profile)["total_runtime_minutes"] == 200


def test_creating_a_movie_does_not_touch_any_cache(profile):
    watch(profile)
    services.get_stats(profile=profile)
    version = profile_cache.get_version(profile.id)

    WatchedMovieFactory()

    assert profile_cache.get_version(profile.id) == version


def test_a_write_of_one_profile_keeps_the_cache_of_the_others(profile):
    other = ProfileFactory()
    watch(other)
    services.get_stats(profile=other)

    watch(profile)

    _, queries = query_count(services.get_stats, profile=other)
    assert queries == 0
