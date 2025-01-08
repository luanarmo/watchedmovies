import math
from datetime import date, timedelta

from django.db.models import Count, Sum

from watchedmovies.services import tmdb_api
from watchedmovies.users.models import Profile

from .models import ViewDetails, WatchedMovie
from .utils import create_wrapped_poster, generate_collage


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


def create_collage(
    *,
    queryset: list,
) -> str:
    """Create a collage from a list of poster URLs."""
    watched_movies = queryset.values_list("poster_path", flat=True)

    return generate_collage(poster_urls=watched_movies)


def get_watched_register_years(*, profile: Profile) -> dict:
    """Get the years in which the user registered watched movies."""
    years = (
        ViewDetails.objects.filter(profile=profile)
        .order_by("-watched_date")
        .values_list("watched_date__year", flat=True)
    )

    unique_years = list(set(years))
    ordered_years = sorted(unique_years, reverse=True)

    return {"years": ordered_years}


def create_wrapped(*, profile: Profile) -> dict:
    """Get statistics from watched movies."""

    current_year = date.today().year

    total_watched_movies = ViewDetails.objects.filter(
        profile=profile,
        watched_date__year=current_year,
    ).count()

    total_minutes_watched = ViewDetails.objects.filter(profile=profile, watched_date__year=current_year).aggregate(
        total_hours=Sum("watched_movie__runtime")
    )["total_hours"]

    total_hours_watched = math.ceil(total_minutes_watched / 60) if total_minutes_watched else 0

    favorite_movie = (
        ViewDetails.objects.filter(profile=profile, watched_date__year=current_year)
        .values("watched_movie__title")
        .annotate(watched_times=Count("watched_movie__title"))
        .order_by("-watched_times")[:1]
    )

    # Filtrar los detalles de las películas y contar las veces que aparece cada género.
    watched_movies_details = ViewDetails.objects.filter(
        profile=profile,
        watched_date__year=current_year,
    ).values("watched_movie__more_details")
    genres = {}
    for movie in watched_movies_details:
        for genre in movie["watched_movie__more_details"]["genres"]:
            genre_name = genre["name"]
            if genre_name in genres:
                genres[genre_name]["count"] += 1
            else:
                genres[genre_name] = {"name": genre_name, "count": 1}

    favorite_genre = max(genres.values(), key=lambda x: x["count"])["name"] if genres else 0

    # Obtener las fechas de visualización
    watched_dates = ViewDetails.objects.filter(profile=profile, watched_date__year=current_year).values_list(
        "watched_date", flat=True
    )

    # Asegurarse de que las fechas estén ordenadas
    watched_dates = sorted(watched_dates)

    # Inicializar las variables para contar la racha más larga
    max_streak = 0
    current_streak = 1  # Iniciar la racha con el primer día

    # Recorrer las fechas para calcular las rachas
    for i in range(1, len(watched_dates)):
        # Si la fecha actual es un día consecutivo al anterior
        if watched_dates[i] - watched_dates[i - 1] == timedelta(days=1):
            current_streak += 1
        else:
            # Si no es consecutivo, reiniciar la racha
            max_streak = max(max_streak, current_streak)
            current_streak = 1

    # Asegurarse de considerar la última racha
    max_streak = max(max_streak, current_streak)

    favorite_movie_title = favorite_movie[0]["watched_movie__title"] if favorite_movie else ""

    wrapped_data = {
        "favorite_movie": {
            "text": "Pelicula favorita: ",
            "value": favorite_movie_title,
        },
        "total_watched_movies": {"text": "Total peliculas: ", "value": total_watched_movies},
        "total_hours_watched": {"text": "Horas vistas: ", "value": total_hours_watched},
        "favorite_genre": {"text": "Genero favorito: ", "value": favorite_genre},
        "max_streak": {"text": "Racha más larga: ", "value": max_streak},
    }

    return create_wrapped_poster(wrapped_data)
