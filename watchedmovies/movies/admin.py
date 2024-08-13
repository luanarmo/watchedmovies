from django.contrib import admin

from watchedmovies.movies.models import WatchedMovie


@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ["title", "release_date", "original_language"]
    list_filter = ["release_date", "original_language"]
    search_fields = ["title"]
