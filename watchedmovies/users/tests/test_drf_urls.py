from django.urls import resolve, reverse


def test_user_register():
    assert reverse("users:anonymous-list") == "/api/anonymous/"
    assert resolve("/api/anonymous/").view_name == "users:anonymous-list"


def test_user_change_password():
    assert reverse("users:anonymous-change_password") == "/api/anonymous/change_password/"
    assert resolve("/api/anonymous/change_password/").view_name == "users:anonymous-change_password"


def test_user_retrieve():
    assert reverse("users:users-detail", kwargs={"pk": 1}) == "/api/users/1/"
    assert resolve("/api/users/1/").view_name == "users:users-detail"
