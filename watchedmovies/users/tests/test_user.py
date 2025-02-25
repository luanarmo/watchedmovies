from unittest.mock import patch

from ..views import AnonymousUserViewset, UserViewSet
from .factories import ProfileFactory, UserFactory

FAKE = "/fake-url/"


def test_register_user(db, api_rf):
    data = {
        "email": "one@test.com",
        "profile": {"bio": "One", "birth_date": "1990-01-01"},
        "password": "TestPassword123",
        "confirm_password": "TestPassword123",
        "token": "fake_token",
    }
    request = api_rf.post(FAKE, data, format="json")

    with patch("watchedmovies.users.views.validate_recaptcha", return_value=True):
        response = AnonymousUserViewset.as_view({"post": "create"})(request)
    assert response.status_code == 201
    assert response.data["detail"] == "User created successfully."


def test_tegister_user_profile_no_data(db, api_rf):
    data = {
        "email": "some@test.com",
        "profile": {},
        "password": "Txxf8M47ODpPUv",
        "confirm_password": "Txxf8M47ODpPUv",
        "token": "fake token",
    }
    request = api_rf.post(FAKE, data, format="json")

    with patch("watchedmovies.users.views.validate_recaptcha", return_value=True):
        response = AnonymousUserViewset.as_view({"post": "create"})(request)

    assert response.status_code == 201
    assert response.data["detail"] == "User created successfully."


def test_register_user_invalid_email(db, api_rf):
    data = {
        "name": "Two Test User",
        "email": "two.com",
        "profile": {"bio": "Two test bio", "birth_date": "1991-01-01"},
        "password": "TestPassword980",
        "confirm_password": "TestPassword980",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = AnonymousUserViewset.as_view({"post": "create"})(request)
    assert response.status_code == 400
    assert response.data["email"][0] == "Enter a valid email address."


def test_register_user_passwords_do_not_match(db, api_rf):
    data = {
        "email": "three@test.com",
        "profile": {"bio": "Three test bio", "birth_date": "1992-01-01"},
        "password": "TestPassword12345",
        "confirm_password": "TestPassword456",
        "token": "fake token",
    }
    request = api_rf.post(FAKE, data, format="json")

    with patch("watchedmovies.users.views.validate_recaptcha", return_value=True):
        response = AnonymousUserViewset.as_view({"post": "create"})(request)

    assert response.status_code == 400
    assert response.data["confirm_password"][0] == "Passwords do not match."


def test_register_user_email_already_exists(db, api_rf):
    user = UserFactory()
    data = {
        "name": "Four Test User",
        "email": user.email,
        "profile": {"bio": "Four test bio", "birth_date": "1993-01-01"},
        "password": "M3swgF3lke9swV",
        "confirm_password": "M3swgF3lke9swV",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = AnonymousUserViewset.as_view({"post": "create"})(request)
    assert response.status_code == 400
    assert response.data["email"][0] == "Email already exists."


def test_register_user_invalid_password(db, api_rf):
    data = {
        "name": "Five Test User",
        "email": "five@test.com",
        "profile": {"bio": "Five test bio", "birth_date": "1994-01-01"},
        "password": "12345",
        "confirm_password": "12345",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = AnonymousUserViewset.as_view({"post": "create"})(request)
    assert response.status_code == 400
    assert response.data["password"][0] == "This password is too short. It must contain at least 9 characters."


def test_register_user_invalid_birth_date(db, api_rf):
    data = {
        "name": "Six Test User",
        "email": "six@test.com",
        "profile": {"bio": "Six test bio", "birth_date": "invalid_date"},
        "password": "AuSlck4Tnyw12y",
        "confirm_password": "AuSlck4Tnyw12y",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = AnonymousUserViewset.as_view({"post": "create"})(request)
    assert response.status_code == 400
    assert (
        response.data["profile"]["birth_date"][0]
        == "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."
    )


def test_register_user_invalid_birth_date_future(db, api_rf):
    data = {
        "name": "Seven Test User",
        "email": "seven@test.com",
        "profile": {"bio": "Seven test bio", "birth_date": "2099-01-01"},
        "password": "AuSlck4Tnyw12z",
        "confirm_password": "AuSlck4Tnyw12z",
    }

    request = api_rf.post(FAKE, data, format="json")
    response = AnonymousUserViewset.as_view({"post": "create"})(request)
    assert response.status_code == 400
    assert response.data["profile"]["birth_date"][0] == "Invalid date - future dates are not allowed."


def test_me(db, api_rf):
    user = UserFactory()
    request = api_rf.get(FAKE)
    request.user = user
    response = UserViewSet.as_view({"get": "me"})(request)
    assert response.status_code == 200
    assert response.data["email"] == user.email


def test_update_user(db, api_rf):
    user = UserFactory()
    ProfileFactory(user=user)
    data = {"name": "Updated Name", "profile": {"bio": "Updated Bio", "birth_date": "1995-01-01"}}
    request = api_rf.put(FAKE, data, format="json")
    request.user = user
    response = UserViewSet.as_view({"put": "update_user"})(request)
    assert response.status_code == 200
    assert response.data["name"] == data["name"]
    assert response.data["profile"]["bio"] == data["profile"]["bio"]
    assert response.data["profile"]["birth_date"] == data["profile"]["birth_date"]


def test_update_user_blank_profile(db, api_rf):
    user = UserFactory()
    ProfileFactory(user=user, bio="Old Bio", birth_date="1996-01-01")
    data = {"name": "Updated Name", "profile": {}}
    request = api_rf.patch(FAKE, data, format="json")
    request.user = user
    response = UserViewSet.as_view({"patch": "update_user"})(request)
    assert response.status_code == 200
    assert response.data["name"] == data["name"]
    assert response.data["profile"]["bio"] == "Old Bio"


def test_delete_user(db, api_rf):
    user = UserFactory()
    ProfileFactory(user=user)
    request = api_rf.delete(FAKE)
    request.user = user
    response = UserViewSet.as_view({"delete": "delete_user"})(request)
    assert response.status_code == 204
