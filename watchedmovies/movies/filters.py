import django_filters
from django.db.models import Avg, Count, Exists, Max, OuterRef, Q

from .models import ViewDetails, WatchedMovie


class WatchedMovieFilter(django_filters.FilterSet):
    """Filter for watched movies."""

    watched_date_year = django_filters.NumberFilter(method="filter_watched_date_year")

    class Meta:
        model = WatchedMovie
        fields = {"title": ["icontains"], "original_title": ["icontains"]}

    def filter_watched_date_year(self, queryset, name, value):
        """Filter watched movies watched in the given year and scope their aggregates to that year.

        Uses Exists instead of filtering through `view_details`: a second filter() on a
        multi-valued relation adds a new JOIN that multiplies the rows the aggregates count.
        The annotations from the viewset's get_queryset are overridden so every aggregate
        only considers the profile's views of the given year.
        """
        profile = self.request.user.profile
        year_views = Q(view_details__profile=profile, view_details__watched_date__year=value)
        year_view_details = ViewDetails.objects.filter(
            watched_movie=OuterRef("pk"),
            profile=profile,
            watched_date__year=value,
        )
        return queryset.filter(Exists(year_view_details)).annotate(
            first_watched_date=Max("view_details__watched_date", filter=year_views),
            total_views=Count("view_details", filter=year_views),
            avg_rating=Avg("view_details__rating", filter=year_views),
            is_favorite=Exists(year_view_details.filter(is_favorite=True)),
        )


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
