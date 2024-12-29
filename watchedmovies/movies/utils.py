import math
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import BinaryIO, Protocol

import requests
from PIL import Image, ImageDraw, ImageFont

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


class TextLine:
    """Clase que representa una línea de texto con sus propiedades."""

    def __init__(
        self,
        text: str,
        font: ImageFont,
        color: tuple[int, int, int],
    ):
        self.text = text
        self.font = font
        self.color = color


class RenderStrategy(Protocol):
    """Interfaz para las estrategias de renderizado."""

    def render(self, canvas: "Canvas", lines: list[TextLine]) -> int:
        """Renderiza el texto en el canvas."""
        pass


class OneColumnRenderStrategy(RenderStrategy):
    """Estrategia de renderizado en una columna."""

    def render(self, canvas: "Canvas", lines: list[TextLine]) -> None:
        for line in lines:
            text_bbox = canvas.draw.textbbox((0, 0), line.text, font=line.font)
            text_height = text_bbox[3] - text_bbox[1]
            canvas.draw.text(
                (canvas.x_pos, canvas.y_pos),
                line.text,
                font=line.font,
                fill=line.color,
            )
            canvas.y_pos += text_height + canvas.y_spacing


class TwoColumnRenderStrategy(RenderStrategy):
    """Estrategia de renderizado en dos columnas."""

    def render(self, canvas: "Canvas", lines: list[TextLine]) -> None:
        odd_lines = lines[::2]
        even_lines = lines[1::2]

        for line1, line2 in zip(odd_lines, even_lines):
            text_bbox1 = canvas.draw.textbbox(
                (0, 0),
                line1.text,
                font=line1.font,
            )
            text_bbox2 = canvas.draw.textbbox(
                (0, 0),
                line2.text,
                font=line2.font,
            )
            text_height1 = text_bbox1[3] - text_bbox1[1]
            text_height2 = text_bbox2[3] - text_bbox2[1]
            canvas.draw.text(
                (canvas.x_pos, canvas.y_pos),
                line1.text,
                font=line1.font,
                fill=line1.color,
            )
            canvas.draw.text(
                (canvas.x_pos + 500, canvas.y_pos),
                line2.text,
                font=line2.font,
                fill=line2.color,
            )
            canvas.y_pos += max(text_height1, text_height2) + canvas.y_spacing


class Canvas:
    """Clase que representa un canvas para renderizar texto."""

    def __init__(
        self,
        bg_img_path: str,
        x_pos: int = 0,
        y_pos: int = 0,
        y_spacing: int = 40,
        strategy: RenderStrategy = OneColumnRenderStrategy(),
    ):
        self.bg_img_path = bg_img_path
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.y_spacing = y_spacing
        self.strategy = strategy
        self.image = Image.open(self.bg_img_path)
        self.draw = ImageDraw.Draw(self.image)

    def set_strategy(self, strategy: RenderStrategy):
        self.strategy = strategy

    def render_text(self, lines: list[TextLine]) -> None:
        """Renderiza el texto en el canvas."""
        self.strategy.render(self, lines)

    def save(self) -> BinaryIO:
        """Guarda y muestra la imagen renderizada."""
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        self.image.save(temp_path.name, "PNG")
        temp_path.seek(0)
        return temp_path.read()


def load_font(path: str, size: int) -> ImageFont:
    """Carga una fuente TrueType desde un archivo."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()
