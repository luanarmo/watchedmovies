from rest_framework.test import APIRequestFactory

from watchedmovies.users.models import User
from watchedmovies.users.views import UserViewSet


def test_me(user: User, api_rf: APIRequestFactory):
    request = api_rf.get("/fake-url/")
    request.user = user

    response = UserViewSet.as_view({"get": "me"})(request)

    assert ["pk", "name", "email", "profile"] == list(response.data.keys())
