from datetime import date

from watchedmovies.users.tests.factories import ProfileFactory

from ..models import MovieTier, ViewDetails
from ..views import WatchedMovieViewSet
from .factories import WatchedMovieFactory

FAKE = "/fake-url/"
THIS_YEAR = date.today().year


def get_tier_list(user, api_rf, params=None):
    request = api_rf.get(FAKE, params or {})
    request.user = user
    return WatchedMovieViewSet.as_view({"get": "tier_list"})(request)


def watch(profile, movie, watched_date, tier=None):
    ViewDetails.objects.create(profile=profile, watched_movie=movie, watched_date=watched_date)
    if tier:
        MovieTier.objects.update_or_create(profile=profile, movie=movie, defaults={"tier": tier})


def test_tier_list_returns_movies_watched_this_year_ordered_by_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    b_movie = WatchedMovieFactory(title="B movie", poster_path="/b.jpg")
    s_movie = WatchedMovieFactory(title="S movie", poster_path="/s.jpg")
    watch(profile, b_movie, date(THIS_YEAR, 1, 10), tier=3)
    watch(profile, s_movie, date(THIS_YEAR, 2, 10), tier=5)

    response = get_tier_list(user, api_rf)

    assert response.status_code == 200
    assert [(m["id"], m["tier"]) for m in response.data] == [(s_movie.id, 5), (b_movie.id, 3)]
    assert response.data[0]["title"] == "S movie"
    assert response.data[0]["poster_url"].endswith("/s.jpg")


def test_tier_list_hides_movies_without_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watch(profile, WatchedMovieFactory(), date(THIS_YEAR, 1, 10))

    response = get_tier_list(user, api_rf)

    assert response.status_code == 200
    assert response.data == []


def test_tier_list_hides_movies_watched_only_in_other_years(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watch(profile, WatchedMovieFactory(), date(THIS_YEAR - 1, 12, 31), tier=5)

    response = get_tier_list(user, api_rf)

    assert response.data == []


def test_tier_list_lists_a_movie_once_when_watched_several_times(db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie = WatchedMovieFactory()
    watch(profile, movie, date(THIS_YEAR, 1, 10), tier=4)
    watch(profile, movie, date(THIS_YEAR, 3, 10))

    response = get_tier_list(user, api_rf)

    assert [m["id"] for m in response.data] == [movie.id]


def test_tier_list_ignores_other_profiles(db, user, api_rf):
    ProfileFactory(user=user)
    other_profile = ProfileFactory()
    watch(other_profile, WatchedMovieFactory(), date(THIS_YEAR, 1, 10), tier=5)

    response = get_tier_list(user, api_rf)

    assert response.data == []


def test_tier_list_returns_movies_watched_in_the_given_year(db, user, api_rf):
    profile = ProfileFactory(user=user)
    old_movie = WatchedMovieFactory()
    watch(profile, old_movie, date(2020, 5, 1), tier=2)
    watch(profile, WatchedMovieFactory(), date(THIS_YEAR, 1, 10), tier=5)

    response = get_tier_list(user, api_rf, {"year": 2020})

    assert response.status_code == 200
    assert [(m["id"], m["tier"]) for m in response.data] == [(old_movie.id, 2)]


def test_tier_list_rejects_an_invalid_year(db, user, api_rf):
    ProfileFactory(user=user)

    response = get_tier_list(user, api_rf, {"year": "abc"})

    assert response.status_code == 400


def set_tier(user, api_rf, movie_id, data):
    request = api_rf.patch(FAKE, data, format="json")
    request.user = user
    return WatchedMovieViewSet.as_view({"patch": "set_tier"})(request, pk=movie_id)


def test_set_tier_changes_the_tier_of_a_watched_movie(db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie = WatchedMovieFactory()
    watch(profile, movie, date(THIS_YEAR, 1, 10), tier=4)

    response = set_tier(user, api_rf, movie.id, {"tier": 5})

    assert response.status_code == 200
    assert response.data == {"tier": 5}
    assert MovieTier.objects.get(profile=profile, movie=movie).tier == 5


def test_set_tier_assigns_a_tier_to_a_movie_without_one(db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie = WatchedMovieFactory()
    watch(profile, movie, date(THIS_YEAR, 1, 10))

    response = set_tier(user, api_rf, movie.id, {"tier": 2})

    assert response.status_code == 200
    assert MovieTier.objects.get(profile=profile, movie=movie).tier == 2


def test_set_tier_rejects_a_tier_out_of_range(transactional_db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie = WatchedMovieFactory()
    watch(profile, movie, date(THIS_YEAR, 1, 10), tier=4)

    for invalid_tier in (0, 6):
        response = set_tier(user, api_rf, movie.id, {"tier": invalid_tier})

        assert response.status_code == 400
    assert MovieTier.objects.get(profile=profile, movie=movie).tier == 4


def test_set_tier_requires_a_tier(transactional_db, user, api_rf):
    profile = ProfileFactory(user=user)
    movie = WatchedMovieFactory()
    watch(profile, movie, date(THIS_YEAR, 1, 10), tier=4)

    for data in ({}, {"tier": None}):
        response = set_tier(user, api_rf, movie.id, data)

        assert response.status_code == 400
    assert MovieTier.objects.get(profile=profile, movie=movie).tier == 4


def test_set_tier_does_not_touch_movies_the_user_has_not_watched(transactional_db, user, api_rf):
    ProfileFactory(user=user)
    other_profile = ProfileFactory()
    movie = WatchedMovieFactory()
    watch(other_profile, movie, date(THIS_YEAR, 1, 10), tier=3)

    response = set_tier(user, api_rf, movie.id, {"tier": 5})

    assert response.status_code == 404
    assert MovieTier.objects.get(profile=other_profile, movie=movie).tier == 3
