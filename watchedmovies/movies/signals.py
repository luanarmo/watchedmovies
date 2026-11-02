from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from . import profile_cache
from .models import MovieTier, ViewDetails, WatchedMovie


@receiver([post_save, post_delete], sender=ViewDetails, dispatch_uid="invalidate_cache_on_view_details_change")
@receiver([post_save, post_delete], sender=MovieTier, dispatch_uid="invalidate_cache_on_movie_tier_change")
def invalidate_profile_cache(sender, instance, **kwargs):
    """Stats, years and tier list of a profile depend on its views and tiers."""
    profile_cache.invalidate_profile(instance.profile_id)


@receiver(post_save, sender=WatchedMovie, dispatch_uid="invalidate_cache_on_watched_movie_change")
def invalidate_profile_cache_on_movie_change(sender, instance, created, **kwargs):
    """Runtime, genres, title and poster come from the movie: refresh every profile that has it.

    A newly created movie has no views or tiers yet, so there is nothing to invalidate."""
    if created:
        return
    profile_ids = set(instance.view_details.values_list("profile_id", flat=True))
    profile_ids.update(instance.tiers.values_list("profile_id", flat=True))
    for profile_id in profile_ids:
        profile_cache.invalidate_profile(profile_id)
