import io
from unittest.mock import MagicMock, patch

import pytest
import requests
from PIL import Image

from .. import utils

REQUESTS_GET = "watchedmovies.movies.utils.requests.get"


def png_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (10, 15), (255, 0, 0)).save(buffer, "PNG")
    return buffer.getvalue()


def fake_response(content=b"", raises=False):
    response = MagicMock()
    response.content = content
    response.raise_for_status.side_effect = requests.HTTPError if raises else None
    return response


@patch(REQUESTS_GET)
def test_poster_is_downloaded_once_and_then_cached(mock_get):
    mock_get.return_value = fake_response(png_bytes())

    first = utils.open_image_generator("/poster.jpg")
    second = utils.open_image_generator("/poster.jpg")

    assert first.size == second.size == (10, 15)
    assert mock_get.call_count == 1


@patch(REQUESTS_GET)
def test_each_poster_has_its_own_cache_entry(mock_get):
    mock_get.return_value = fake_response(png_bytes())

    utils.open_image_generator("/a.jpg")
    utils.open_image_generator("/b.jpg")

    assert mock_get.call_count == 2


@patch(REQUESTS_GET)
def test_failed_poster_downloads_are_not_cached(mock_get):
    mock_get.return_value = fake_response(raises=True)

    with pytest.raises(requests.HTTPError):
        utils.open_image_generator("/poster.jpg")
    with pytest.raises(requests.HTTPError):
        utils.open_image_generator("/poster.jpg")

    assert mock_get.call_count == 2
