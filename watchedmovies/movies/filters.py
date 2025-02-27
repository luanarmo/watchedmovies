import django_filters

from .models import ViewDetails, WatchedMovie


class WatchedMovieFilter(django_filters.FilterSet):
    """Filter for watched movies."""

    watched_date_year = django_filters.NumberFilter(method="filter_watched_date_year")

    class Meta:
        model = WatchedMovie
        fields = {"title": ["icontains"], "original_title": ["icontains"]}

    def filter_watched_date_year(self, queryset, name, value):
        """Filter watched movies by first watched date."""
        return queryset.filter(view_details__watched_date__year=value, view_details__profile=self.request.user.profile)


class ViewDetailFilter(django_filters.FilterSet):
    """Filter for view details."""

    watched = django_filters.NumberFilter(field_name="watched_movie__id", lookup_expr="exact")

    class Meta:
        model = ViewDetails
        fields = {
            "rating": ["exact", "gt", "lt"],
            "language": ["icontains"],
            "place": ["icontains"],
        }
