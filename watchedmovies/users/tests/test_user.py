from .factories import UserFactory, ProfileFactory
from ..views import RegisterUserView, me, update, change_password, delete
from rest_framework.test import APIRequestFactory
from watchedmovies.users.models import User
import pytest

FAKE = "/fake-url/"


@pytest.fixture
def api_rf() -> APIRequestFactory:
    return APIRequestFactory()


def test_register_user(db, api_rf):
    data = {
        "name": "One Test User",
        "email": "one@test.com",
        "profile": {"bio": "One", "birth_date": "1990-01-01"},
        "password": "TestPassword123",
        "password2": "TestPassword123",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = RegisterUserView.as_view()(request)
    assert response.status_code == 201


def test_tegister_user_profile_no_data(db, api_rf):
    data = {
        "name": "Some Test User",
        "email": "some@test.com",
        "profile": {},
        "password": "Txxf8M47ODpPUv",
        "password2": "Txxf8M47ODpPUv",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = RegisterUserView.as_view()(request)
    assert response.status_code == 201


def test_register_user_invalid_email(db, api_rf):
    data = {
        "name": "Two Test User",
        "email": "two.com",
        "profile": {"bio": "Two test bio", "birth_date": "1991-01-01"},
        "password": "TestPassword980",
        "password2": "TestPassword980",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = RegisterUserView.as_view()(request)
    assert response.status_code == 400
    assert response.data["email"][0] == "Enter a valid email address."


def test_register_user_passwords_do_not_match(db, api_rf):
    data = {
        "name": "Three Test User",
        "email": "three@test.com",
        "profile": {"bio": "Three test bio", "birth_date": "1992-01-01"},
        "password": "TestPassword12345",
        "password2": "TestPassword456",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = RegisterUserView.as_view()(request)
    assert response.status_code == 400
    assert response.data["password"][0] == "Passwords do not match."


def test_register_user_email_already_exists(db, api_rf):
    user = UserFactory()
    data = {
        "name": "Four Test User",
        "email": user.email,
        "profile": {"bio": "Four test bio", "birth_date": "1993-01-01"},
        "password": "M3swgF3lke9swV",
        "password2": "M3swgF3lke9swV",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = RegisterUserView.as_view()(request)
    assert response.status_code == 400
    assert response.data["email"][0] == "Email already exists."


def test_register_user_invalid_password(db, api_rf):
    data = {
        "name": "Five Test User",
        "email": "five@test.com",
        "profile": {"bio": "Five test bio", "birth_date": "1994-01-01"},
        "password": "12345",
        "password2": "12345",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = RegisterUserView.as_view()(request)
    assert response.status_code == 400
    assert response.data["password"][0] == "This password is too short. It must contain at least 9 characters."


def test_register_user_invalid_birth_date(db, api_rf):
    data = {
        "name": "Six Test User",
        "email": "six@test.com",
        "profile": {"bio": "Six test bio", "birth_date": "invalid_date"},
        "password": "AuSlck4Tnyw12y",
        "password2": "AuSlck4Tnyw12y",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = RegisterUserView.as_view()(request)
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
        "password2": "AuSlck4Tnyw12z",
    }

    request = api_rf.post(FAKE, data, format="json")
    response = RegisterUserView.as_view()(request)
    assert response.status_code == 400
    assert response.data["profile"]["birth_date"][0] == "Invalid date - future dates are not allowed."


def test_me(db, api_rf):
    user = UserFactory()
    request = api_rf.get(FAKE)
    request.user = user
    response = me(request)
    assert response.status_code == 200
    assert response.data["email"] == user.email


def test_update_user(db, api_rf):
    user = UserFactory()
    ProfileFactory(user=user)
    data = {"name": "Updated Name", "profile": {"bio": "Updated Bio", "birth_date": "1995-01-01"}}
    request = api_rf.patch(FAKE, data, format="json")
    request.user = user
    response = update(request)
    assert response.status_code == 200
    assert response.data["name"] == data["name"]


def test_update_user_blank_profile(db, api_rf):
    user = UserFactory()
    ProfileFactory(user=user)
    data = {"name": "Updated Name", "profile": {}}
    request = api_rf.patch(FAKE, data, format="json")
    request.user = user
    response = update(request)
    assert response.status_code == 200
    assert response.data["name"] == data["name"]


def test_change_password(db, api_rf):
    passw = "5ng1jBsG4lt9gB"
    new_passw = "NewPassword123"
    user = UserFactory(password=passw, email="random@test.com")
    ProfileFactory(user=user)
    data = {
        "email": user.email,
        "old_password": passw,
        "new_password": new_passw,
        "confirm_password": new_passw,
    }
    request = api_rf.post(FAKE, data, format="json")
    response = change_password(request)
    assert response.status_code == 200
    assert response.data["detail"] == "Password changed successfully."
    user.refresh_from_db()
    assert user.check_password(new_passw) is True


def test_change_password_invalid_old_password(db, api_rf):
    passw = "5ng1jBsG4lt9gC"
    user = UserFactory(password=passw, email="ten@test.com")
    ProfileFactory(user=user)
    data = {
        "email": user.email,
        "old_password": "InvalidOldPassword",
        "new_password": "NewPassword124",
        "confirm_password": "NewPassword124",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = change_password(request)
    assert response.status_code == 400
    assert response.data["old_password"][0] == "Old password is incorrect."


def test_change_password_invalid_same_password(db, api_rf):
    passw = "5ng1jBsG4lt9gD"
    user = UserFactory(password=passw, email="eleven@test.com")
    ProfileFactory(user=user)
    data = {
        "email": user.email,
        "old_password": passw,
        "new_password": passw,
        "confirm_password": passw,
    }
    request = api_rf.post(FAKE, data, format="json")
    response = change_password(request)
    assert response.status_code == 400
    assert response.data["new_password"][0] == "New password must be different from old password."


def test_change_password_invalid_confirm_password(db, api_rf):
    passw = "5ng1jBsG4lt9gD"
    user = UserFactory(password=passw, email="twelve@test.com")
    ProfileFactory(user=user)
    data = {
        "email": user.email,
        "old_password": passw,
        "new_password": "5ng1jBsG4lt9gE",
        "confirm_password": "InvalidConfirmPassword",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = change_password(request)
    assert response.status_code == 400
    assert response.data["confirm_password"][0] == "Passwords do not match."


def test_change_password_invalid_email(db, api_rf):
    passw = "5ng1jBsG4lt9gF"
    user = UserFactory(password=passw, email="fourteen@test.com")
    ProfileFactory(user=user)
    data = {
        "email": "not_exist@email.com",
        "old_password": passw,
        "new_password": "NewPassword125",
        "confirm_password": "NewPassword125",
    }
    request = api_rf.post(FAKE, data, format="json")
    response = change_password(request)
    assert response.status_code == 400
    assert response.data["email"][0] == "User does not exist."


def test_delete_user(db, api_rf):
    user = UserFactory()
    ProfileFactory(user=user)
    request = api_rf.delete(FAKE)
    request.user = user
    response = delete(request)
    assert response.status_code == 204
    assert response.data["detail"] == "User account deleted."
    assert User.objects.filter(pk=user.pk).exists() is False
