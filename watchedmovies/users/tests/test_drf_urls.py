from django.urls import resolve, reverse


def test_user_register():
    assert reverse("users:anonymous-list") == "/api/anonymous/"
    assert resolve("/api/anonymous/").view_name == "users:anonymous-list"


def test_user_change_password():
    assert reverse("users:anonymous-change_password") == "/api/anonymous/change_password/"
    assert resolve("/api/anonymous/change_password/").view_name == "users:anonymous-change_password"


def test_user_retrieve():
    assert reverse("users:users-me") == "/api/users/me/"
    assert resolve("/api/users/me/").view_name == "users:users-me"


def test_user_update():
    assert reverse("users:users-update_user") == "/api/users/update_user/"
    assert resolve("/api/users/update_user/").view_name == "users:users-update_user"


def test_user_partial_update():
    assert reverse("users:users-partial_update_user") == "/api/users/partial_update_user/"
    assert resolve("/api/users/partial_update_user/").view_name == "users:users-partial_update_user"


def test_user_delete():
    assert reverse("users:users-delete_user") == "/api/users/delete_user/"
    assert resolve("/api/users/delete_user/").view_name == "users:users-delete_user"
