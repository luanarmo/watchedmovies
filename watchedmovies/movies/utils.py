import math
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import BinaryIO

import requests
from PIL import Image

from config.settings.base import env

from . import ImageSizes


def get_poster_path(image_path: str, size: str = "w342") -> str:
    """Return the full URL of an image from the TMDB API."""
    base_url = env("TMDB_SECURE_BASE_URL")
    if size not in ImageSizes.POSTER_SIZES:
        raise ValueError(f"Invalid image size: {size}")
    return f"{base_url}{size}{image_path}"


def get_backdrop_path(image_path: str, size: str = "w780") -> str:
    """Return the full URL of a backdrop image from the TMDB API."""
    base_url = env("TMDB_SECURE_BASE_URL")
    if size not in ImageSizes.BACKDROP_SIZES:
        raise ValueError(f"Invalid image size: {size}")
    return f"{base_url}{size}{image_path}"


def generate_collage(*, poster_urls: list) -> BinaryIO:
    """Generate a collage from a list of poster URLs."""

    WIDTH = env("COLLAGE_WIDTH", default=300)
    HEIGHT = env("COLLAGE_HEIGHT", default=450)

    # Fetch and open images concurrently
    with ThreadPoolExecutor() as executor:
        images = list(executor.map(open_image_generator, poster_urls))

    # Calculate the number of rows and columns
    n = len(images)
    cols, rows = calculate_dimensions(n)

    # Create base image
    collage = Image.new("RGB", (cols * WIDTH, rows * HEIGHT))

    # Paste images
    for idx, img in enumerate(images):
        x = WIDTH * (idx % cols)
        y = HEIGHT * (idx // cols)
        igm_resized = img.resize((WIDTH, HEIGHT))
        collage.paste(igm_resized, (x, y))

    # Save the collage to a temporary file
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpeg")
    collage.save(temp_path.name, "JPEG")
    temp_path.seek(0)
    return temp_path.read()


def open_image_generator(image_path: str) -> Image:
    """Open an image from a file path."""
    path = get_poster_path(image_path)
    response = requests.get(path, stream=True).raw
    return Image.open(response)


def calculate_dimensions(n: int) -> tuple:
    """Calculate the number of rows and columns for a collage."""
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows
