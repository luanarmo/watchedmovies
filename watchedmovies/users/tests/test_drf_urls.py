from django.urls import resolve, reverse


def test_user_register():
    assert reverse("users:register") == "/api/users/register/"
    assert resolve("/api/users/register/").view_name == "users:register"


def test_user_change_password():
    assert reverse("users:change_password") == "/api/users/change_password/"
    assert resolve("/api/users/change_password/").view_name == "users:change_password"


def test_user_delete_profile():
    assert reverse("users:delete_profile") == "/api/users/delete_profile/"
    assert resolve("/api/users/delete_profile/").view_name == "users:delete_profile"


def test_user_me():
    assert reverse("users:me") == "/api/users/me/"
    assert resolve("/api/users/me/").view_name == "users:me"


def test_user_upate_profile():
    assert reverse("users:update_profile") == "/api/users/update_profile/"
    assert resolve("/api/users/update_profile/").view_name == "users:update_profile"
