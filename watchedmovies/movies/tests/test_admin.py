from django.urls import reverse

from watchedmovies.movies.models import WatchedMovie
from watchedmovies.users.tests.factories import ProfileFactory


class TestWatchedMovieAdmin:
    def test_change_list(self, admin_client):
        url = reverse("admin:movies_watchedmovie_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_search(self, admin_client):
        url = reverse("admin:movies_watchedmovie_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == 200

    def test_add(self, admin_client):
        url = reverse("admin:movies_watchedmovie_add")
        response = admin_client.get(url)
        assert response.status_code == 200
        profile = ProfileFactory()
        response = admin_client.post(
            url,
            data={
                "profile": profile.pk,
                "backdrop_path": "a",
                "genre_ids": "[1, 2, 3]",
                "original_language": "en",
                "original_title": "TestMovie",
                "overview": "Test overview",
                "popularity": 0,
                "poster_path": "path",
                "release_date": "01/07/2024",
                "title": "TestMovie",
                "vote_average": 0,
                "vote_count": 100,
                "times_watched": 1,
            },
        )

        assert response.status_code == 302
        assert WatchedMovie.objects.filter(title="TestMovie").exists()
