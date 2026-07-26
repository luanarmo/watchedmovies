import calendar as cal
import math
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.db.models.functions import ExtractMonth, ExtractWeekDay, ExtractYear
from rest_framework.exceptions import ValidationError

from watchedmovies.services import tmdb_api
from watchedmovies.users.models import Profile

from .models import PlanToWatch, ViewDetails, WatchedMovie
from .utils import create_wrapped_poster, generate_collage


@transaction.atomic
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
    """Create a new view detail with the given data and remove the movie from the plan to watch list if it exists."""
    watched_movie = get_or_create_watched_movie(watched_movie=watched_movie)
    delete_from_plan_to_watch(movie_id=watched_movie.id, profile=profile)
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


def delete_from_plan_to_watch(*, movie_id: int, profile: any) -> None:
    """Delete a movie from the plan to watch list."""
    plan = PlanToWatch.objects.filter(movie__id=movie_id, profile=profile).first()

    if not plan:
        return None

    plan.delete()


@transaction.atomic
def create_plan_to_watch(*, movie: dict, profile: any) -> PlanToWatch:
    """Create a new plan to watch with the given data."""
    movie = get_or_create_watched_movie(watched_movie=movie)

    # Check if the movie is already in the plan to watch list or watched list
    if PlanToWatch.objects.filter(movie=movie, profile=profile).exists():
        raise ValidationError("This movie is already in your plan to watch list.")

    if ViewDetails.objects.filter(watched_movie=movie, profile=profile).exists():
        raise ValidationError("This movie is already in your watched list.")

    plan_to_watch = PlanToWatch(
        movie=movie,
        profile=profile,
    )
    plan_to_watch.full_clean()
    plan_to_watch.save()
    return plan_to_watch


def retrieve_plan_to_watch_by_movie_id(*, movie_id: int, profile: any) -> PlanToWatch:
    """Retrieve a plan to watch by movie ID."""
    plan = PlanToWatch.objects.filter(movie__id=movie_id, profile=profile).first()
    if not plan:
        raise ValidationError("This movie is not in your plan to watch list.")
    return plan


def get_or_create_watched_movie(*, watched_movie: dict) -> WatchedMovie:
    """Get or create a watched movie with the given data."""
    original_title = watched_movie.get("original_title")
    title = watched_movie.get("title")
    release_date = watched_movie.get("release_date")

    movie_exists = None

    if original_title:
        movie_exists = WatchedMovie.objects.filter(original_title=original_title, release_date=release_date).first()

    if not movie_exists and title:
        movie_exists = WatchedMovie.objects.filter(title=title, release_date=release_date).first()

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


def create_wrapped(*, profile: Profile, year: int) -> dict:
    """Get statistics from watched movies."""

    year = year if year else date.today().year

    total_watched_movies = ViewDetails.objects.filter(
        profile=profile,
        watched_date__year=year,
    ).count()

    total_minutes_watched = ViewDetails.objects.filter(profile=profile, watched_date__year=year).aggregate(
        total_hours=Sum("watched_movie__runtime")
    )["total_hours"]

    total_hours_watched = math.ceil(total_minutes_watched / 60) if total_minutes_watched else 0

    favorite_movie = (
        ViewDetails.objects.filter(profile=profile, watched_date__year=year)
        .values("watched_movie__title")
        .annotate(watched_times=Count("watched_movie__title"))
        .order_by("-watched_times")[:1]
    )

    # Filtrar los detalles de las películas y contar las veces que aparece cada género.
    watched_movies_details = ViewDetails.objects.filter(
        profile=profile,
        watched_date__year=year,
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
    watched_dates = ViewDetails.objects.filter(profile=profile, watched_date__year=year).values_list(
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


def get_stats(*, profile: Profile, year: int = None) -> dict:
    """Return JSON statistics for the user's watched movies."""
    current_year = date.today().year
    year = int(year) if year else current_year

    base_qs = ViewDetails.objects.filter(profile=profile, watched_date__year=year)
    all_qs = ViewDetails.objects.filter(profile=profile)

    # Totals
    total_watched = base_qs.count()
    total_unique_movies = base_qs.values("watched_movie").distinct().count()
    rewatch_count = total_watched - total_unique_movies
    total_runtime_minutes = base_qs.aggregate(total=Sum("watched_movie__runtime"))["total"] or 0

    avg_raw = base_qs.aggregate(avg=Avg("rating"))["avg"]
    average_rating = round(float(avg_raw), 1) if avg_raw else None

    # Top 5 most-rewatched movies
    favorite_movie_qs = base_qs.values("watched_movie__title").annotate(count=Count("id")).order_by("-count")[:5]
    favorite_movie = [{"title": m["watched_movie__title"], "count": m["count"]} for m in favorite_movie_qs]

    # Genres from more_details JSON
    genres: dict = {}
    for row in base_qs.values("watched_movie__more_details"):
        details = row.get("watched_movie__more_details") or {}
        for genre in details.get("genres", []):
            name = genre.get("name")
            if name:
                genres[name] = genres.get(name, 0) + 1

    genres_list = sorted([{"name": n, "count": c} for n, c in genres.items()], key=lambda x: x["count"], reverse=True)
    favorite_genre = genres_list[0]["name"] if genres_list else None

    # By language
    language_labels = dict(ViewDetails.LANGUAGE_CHOICES)
    by_language = [
        {"key": row["language"], "label": language_labels.get(row["language"], row["language"]), "count": row["count"]}
        for row in base_qs.values("language").annotate(count=Count("id")).order_by("-count")
        if row["language"]
    ]

    # By place
    place_labels = dict(ViewDetails.PLACE_CHOICES)
    by_place = [
        {"key": row["place"], "label": place_labels.get(row["place"], row["place"]), "count": row["count"]}
        for row in base_qs.values("place").annotate(count=Count("id")).order_by("-count")
        if row["place"]
    ]

    # By rating — always 1-10, fill missing with 0
    rating_counts = {
        row["rating"]: row["count"]
        for row in base_qs.values("rating").annotate(count=Count("id"))
        if row["rating"] is not None
    }
    by_rating = [{"rating": r, "count": rating_counts.get(r, 0)} for r in range(1, 11)]

    # By month — always 12 entries
    month_counts = {
        row["month"]: row["count"]
        for row in base_qs.filter(watched_date__isnull=False)
        .annotate(month=ExtractMonth("watched_date"))
        .values("month")
        .annotate(count=Count("id"))
    }
    by_month = [{"month": cal.month_abbr[m], "month_number": m, "count": month_counts.get(m, 0)} for m in range(1, 13)]
    most_active_month_entry = max(by_month, key=lambda x: x["count"]) if any(x["count"] for x in by_month) else None
    most_active_month = (
        most_active_month_entry["month"] if most_active_month_entry and most_active_month_entry["count"] > 0 else None
    )

    # By day of week — Django ExtractWeekDay: 1=Sunday … 7=Saturday
    dow_names = {1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday", 7: "Saturday"}
    dow_counts = {
        row["dow"]: row["count"]
        for row in base_qs.filter(watched_date__isnull=False)
        .annotate(dow=ExtractWeekDay("watched_date"))
        .values("dow")
        .annotate(count=Count("id"))
    }
    by_day_of_week = [{"day": dow_names[d], "day_number": d, "count": dow_counts.get(d, 0)} for d in range(1, 8)]

    # By year — all-time, no year filter, includes avg_rating
    by_year = [
        {
            "year": row["year"],
            "count": row["count"],
            "avg_rating": round(float(row["avg_rating"]), 1) if row["avg_rating"] else None,
        }
        for row in all_qs.filter(watched_date__isnull=False)
        .annotate(year=ExtractYear("watched_date"))
        .values("year")
        .annotate(count=Count("id"), avg_rating=Avg("rating"))
        .order_by("year")
    ]

    # Streak — deduplicate same-day entries
    raw_dates = list(base_qs.filter(watched_date__isnull=False).values_list("watched_date", flat=True))
    unique_dates = sorted(set(raw_dates))

    max_streak = 0
    max_start = None
    max_end = None

    if unique_dates:
        cur_streak = 1
        cur_start = unique_dates[0]

        for i in range(1, len(unique_dates)):
            if unique_dates[i] - unique_dates[i - 1] == timedelta(days=1):
                cur_streak += 1
            else:
                if cur_streak > max_streak:
                    max_streak = cur_streak
                    max_start = cur_start
                    max_end = unique_dates[i - 1]
                cur_streak = 1
                cur_start = unique_dates[i]

        if cur_streak > max_streak:
            max_streak = cur_streak
            max_start = cur_start
            max_end = unique_dates[-1]

    return {
        "year": year,
        "total_watched": total_watched,
        "total_unique_movies": total_unique_movies,
        "rewatch_count": rewatch_count,
        "total_runtime_minutes": total_runtime_minutes,
        "average_rating": average_rating,
        "favorite_movie": favorite_movie,
        "favorite_genre": favorite_genre,
        "most_active_month": most_active_month,
        "max_streak": {
            "days": max_streak,
            "start_date": max_start.isoformat() if max_start else None,
            "end_date": max_end.isoformat() if max_end else None,
        },
        "genres": genres_list,
        "by_language": by_language,
        "by_place": by_place,
        "by_rating": by_rating,
        "by_month": by_month,
        "by_day_of_week": by_day_of_week,
        "by_year": by_year,
    }
