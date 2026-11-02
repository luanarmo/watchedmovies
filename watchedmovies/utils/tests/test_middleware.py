import brotli
from django.http import HttpResponse
from django.test import RequestFactory

from watchedmovies.utils.middleware import SkipImagesCompressionMiddleware

BODY = b'{"title": "Movie", "tier": 5}' * 100


def _process(content_type, accept_encoding, body=BODY):
    request = RequestFactory().get("/", HTTP_ACCEPT_ENCODING=accept_encoding)
    response = HttpResponse(body, content_type=content_type)
    return SkipImagesCompressionMiddleware(lambda r: response).process_response(request, response)


def test_compresses_json_with_brotli():
    response = _process("application/json", "br, gzip")

    assert response["Content-Encoding"] == "br"
    assert "Accept-Encoding" in response["Vary"]
    assert brotli.decompress(response.content) == BODY


def test_falls_back_to_gzip():
    response = _process("application/json", "gzip")

    assert response["Content-Encoding"] == "gzip"


def test_does_not_compress_without_accept_encoding():
    response = _process("application/json", "")

    assert "Content-Encoding" not in response
    assert response.content == BODY


def test_skips_images():
    for content_type in ("image/jpeg", "image/png"):
        response = _process(content_type, "br, gzip")

        assert "Content-Encoding" not in response
        assert response.content == BODY
