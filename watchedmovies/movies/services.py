from datetime import date

from django.db.models import Min

from watchedmovies.services import tmdb_api
from watchedmovies.users.models import Profile

from .models import ViewDetails, WatchedMovie
from .utils import generate_collage


def create_view_detail(
    *,
    watched_movie: dict,
    profile: any,
    rating: int = None,
    comment: str,
    language: str,
    place: str,
    watched_date: date,
) -> ViewDetails:
    """Create a new view detail with the given data."""
    watched_movie = get_or_create_watched_movie(watched_movie=watched_movie)
    view_detail = ViewDetails(
        watched_movie=watched_movie,
        profile=profile,
        rating=rating,
        comment=comment,
        language=language,
        place=place,
        watched_date=watched_date,
    )
    view_detail.full_clean()
    view_detail.save()
    return view_detail


def get_or_create_watched_movie(*, watched_movie: dict) -> WatchedMovie:
    """Get or create a watched movie with the given data."""
    original_title = watched_movie.get("original_title")
    release_date = watched_movie.get("release_date")
    movie_exists = WatchedMovie.objects.filter(original_title=original_title, release_date=release_date).first()

    if movie_exists:
        return movie_exists

    movie = WatchedMovie(**watched_movie)
    movie_details = tmdb_api.get_movie_details(watched_movie.get("id"))

    if movie_details:
        movie.runtime = movie_details.get("runtime")
        movie.more_details = movie_details

    movie.full_clean()
    movie.save()

    return movie


def destroy_view_detail(*, watched_movie: WatchedMovie, profile) -> None:
    """Delete the view details of the given watched movie."""
    ViewDetails.objects.filter(watched_movie=watched_movie, profile=profile).delete()


def create_collage(*, profile: Profile) -> str:
    """Create a collage from a list of poster URLs."""
    watched_movies = (
        WatchedMovie.objects.filter(view_details__profile=profile)
        .annotate(first_watched_date=Min("view_details__watched_date"))
        .order_by("-first_watched_date")
        .values_list("poster_path", flat=True)
    )

    return generate_collage(poster_urls=watched_movies)


def get_watched_register_years(*, profile: Profile) -> dict:
    """Get the years in which the user registered watched movies."""
    years = ViewDetails.objects.filter(profile=profile).values_list("watched_at__year", flat=True)
    return {"years": list(set(years))}
