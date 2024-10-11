from watchedmovies.services import tmdb_api
from .models import ViewDetails, WatchedMovie


def create_view_detail(
    *,
    watched_movie: dict,
    profile: any,
    rating: int = None,
    comment: str,
    language: str,
    place: str,
) -> ViewDetails:
    """Create a new view detail with the given data."""
    watched_movie = get_or_create_watched_movie(watched_movie=watched_movie)
    view_detail = ViewDetails(
        watched_movie=watched_movie, profile=profile, rating=rating, comment=comment, language=language, place=place
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
