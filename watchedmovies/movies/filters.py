import django_filters

from .models import ViewDetails, WatchedMovie


class WatchedMovieFilter(django_filters.FilterSet):
    """Filter for watched movies."""

    class Meta:
        model = WatchedMovie
        fields = {
            "title": ["exact", "icontains"],
            "original_title": ["exact", "icontains"],
            "release_date": ["exact", "year__gt", "year__lt"],
            "vote_average": ["exact", "gt", "lt"],
            "popularity": ["exact", "gt", "lt"],
        }


class ViewDetailFilter(django_filters.FilterSet):
    """Filter for view details."""

    class Meta:
        model = ViewDetails
        fields = {
            "rating": ["exact", "gt", "lt"],
            "language": ["icontains"],
            "place": ["icontains"],
        }
