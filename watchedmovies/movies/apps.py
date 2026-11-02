from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MoviesConfig(AppConfig):
    name = "watchedmovies.movies"
    verbose_name = _("Movies")

    def ready(self):
        from . import signals  # noqa: F401  (connects the cache invalidation receivers)
