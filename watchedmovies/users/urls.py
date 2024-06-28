from django.urls import path

from watchedmovies.users import views

app_name = "users"

urlpatterns = [
    path("register/", views.register_user, name="register"),
    path("me/", views.me, name="me"),
    path("update_profile/", views.update, name="update_profile"),
    path("change_password/", views.change_password, name="change_password"),
    path("delete_profile/", views.delete, name="delete_profile"),
]
