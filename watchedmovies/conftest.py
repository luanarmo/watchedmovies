import pytest
from rest_framework.test import APIRequestFactory

from watchedmovies.movies.models import WatchedMovie
from watchedmovies.movies.tests.factories import WatchedMovieFactory
from watchedmovies.users.models import User
from watchedmovies.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def watchedmovie(db) -> WatchedMovie:
    return WatchedMovieFactory()


@pytest.fixture
def api_rf() -> APIRequestFactory:
    return APIRequestFactory()
