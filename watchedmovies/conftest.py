import pytest
from django.core.cache import cache
from rest_framework.test import APIRequestFactory

from watchedmovies.movies.models import WatchedMovie
from watchedmovies.movies.tests.factories import WatchedMovieFactory
from watchedmovies.users.models import User
from watchedmovies.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture(autouse=True)
def clear_cache():
    """The test cache (LocMemCache) lives for the whole process: start every test with it empty."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def watchedmovie(db) -> WatchedMovie:
    return WatchedMovieFactory()


@pytest.fixture
def api_rf() -> APIRequestFactory:
    return APIRequestFactory()
