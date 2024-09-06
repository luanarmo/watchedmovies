from config.settings.base import env

from . import ImageSizes


def get_poster_url(image_path: str, size: str = "original") -> str:
    """Return the full URL of an image from the TMDB API."""
    base_url = env("TMDB_SECURE_BASE_URL")
    if size not in ImageSizes.POSTER_SIZES:
        raise ValueError(f"Invalid image size: {size}")
    return f"{base_url}{size}{image_path}"


def get_backdrop_url(image_path: str, size: str = "original") -> str:
    """Return the full URL of a backdrop image from the TMDB API."""
    base_url = env("TMDB_SECURE_BASE_URL")
    if size not in ImageSizes.BACKDROP_SIZES:
        raise ValueError(f"Invalid image size: {size}")
    return f"{base_url}{size}{image_path}"
