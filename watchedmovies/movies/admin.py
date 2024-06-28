from django.contrib import admin

from watchedmovies.movies.models import WatchedMovie


@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ["profile", "watched_at", "times_watched"]
    list_filter = ["watched_at", "times_watched"]
    search_fields = ["profile__user__email", "title"]
