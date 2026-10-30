import base64
import io
from datetime import date

import pytest
from PIL import Image

from watchedmovies.users.tests.factories import ProfileFactory

from ..models import MovieTier, ViewDetails
from ..views import WatchedMovieViewSet
from .factories import WatchedMovieFactory

FAKE = "/fake-url/"
THIS_YEAR = date.today().year

# Layout of the image: a 100px column with the tier letter, then the posters (100x150) of each tier
LETTER_WIDTH = 100
POSTER_WIDTH = 100
POSTER_HEIGHT = 150
TIER_ROWS = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}

RED = (255, 0, 0)
BLUE = (0, 0, 255)


class FakeResponse:
    def __init__(self, color):
        self.raw = io.BytesIO()
        Image.new("RGB", (500, 750), color).save(self.raw, "PNG")
        self.raw.seek(0)


@pytest.fixture(autouse=True)
def fake_posters(monkeypatch):
    """Every poster is a solid color, picked by its path, so the test can tell them apart in the image."""
    colors = {"/red.jpg": RED, "/blue.jpg": BLUE}
    monkeypatch.setattr(
        "watchedmovies.movies.utils.requests.get",
        lambda url, **kwargs: FakeResponse(next(color for path, color in colors.items() if url.endswith(path))),
    )


def get_tier_list_image(user, api_rf, params=None):
    request = api_rf.get(FAKE, params or {})
    request.user = user
    return WatchedMovieViewSet.as_view({"get": "tier_list_image"})(request)


def open_image(response):
    return Image.open(io.BytesIO(base64.b64decode(response.data["image"])))


def watch(profile, movie, watched_date, tier=None):
    ViewDetails.objects.create(profile=profile, watched_movie=movie, watched_date=watched_date)
    if tier:
        MovieTier.objects.update_or_create(profile=profile, movie=movie, defaults={"tier": tier})


def poster_color(image, tier_letter, position=0):
    """Color at the center of the nth poster (from the left) of a tier row."""
    x = LETTER_WIDTH + position * POSTER_WIDTH + POSTER_WIDTH // 2
    y = TIER_ROWS[tier_letter] * POSTER_HEIGHT + POSTER_HEIGHT // 2
    return image.getpixel((x, y))


def test_tier_list_image_returns_a_png_encoded_in_base64(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watch(profile, WatchedMovieFactory(poster_path="/red.jpg"), date(THIS_YEAR, 1, 10), tier=5)

    response = get_tier_list_image(user, api_rf)

    assert response.status_code == 200
    assert open_image(response).format == "PNG"


def test_tier_list_image_puts_each_poster_in_the_row_of_its_tier(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watch(profile, WatchedMovieFactory(poster_path="/red.jpg"), date(THIS_YEAR, 1, 10), tier=5)
    watch(profile, WatchedMovieFactory(poster_path="/blue.jpg"), date(THIS_YEAR, 2, 10), tier=3)

    image = open_image(get_tier_list_image(user, api_rf))

    assert poster_color(image, "S") == RED
    assert poster_color(image, "B") == BLUE


def test_tier_list_image_orders_posters_of_a_tier_by_title(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watch(profile, WatchedMovieFactory(title="B movie", poster_path="/blue.jpg"), date(THIS_YEAR, 1, 10), tier=4)
    watch(profile, WatchedMovieFactory(title="A movie", poster_path="/red.jpg"), date(THIS_YEAR, 2, 10), tier=4)

    image = open_image(get_tier_list_image(user, api_rf))

    assert poster_color(image, "A", position=0) == RED
    assert poster_color(image, "A", position=1) == BLUE


def test_tier_list_image_defaults_to_this_year(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watch(profile, WatchedMovieFactory(poster_path="/blue.jpg"), date(THIS_YEAR - 1, 12, 31), tier=5)
    watch(profile, WatchedMovieFactory(poster_path="/red.jpg"), date(THIS_YEAR, 1, 10), tier=5)

    image = open_image(get_tier_list_image(user, api_rf))

    assert poster_color(image, "S", position=0) == RED
    assert image.width == LETTER_WIDTH + POSTER_WIDTH


def test_tier_list_image_returns_only_the_given_year(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watch(profile, WatchedMovieFactory(poster_path="/blue.jpg"), date(2020, 5, 1), tier=2)
    watch(profile, WatchedMovieFactory(poster_path="/red.jpg"), date(THIS_YEAR, 1, 10), tier=5)

    image = open_image(get_tier_list_image(user, api_rf, {"year": 2020}))

    assert poster_color(image, "C") == BLUE
    assert poster_color(image, "S") != RED


def test_tier_list_image_returns_every_year_with_all(db, user, api_rf):
    profile = ProfileFactory(user=user)
    watch(profile, WatchedMovieFactory(poster_path="/blue.jpg"), date(2020, 5, 1), tier=2)
    watch(profile, WatchedMovieFactory(poster_path="/red.jpg"), date(THIS_YEAR, 1, 10), tier=5)

    image = open_image(get_tier_list_image(user, api_rf, {"year": "all"}))

    assert poster_color(image, "C") == BLUE
    assert poster_color(image, "S") == RED
