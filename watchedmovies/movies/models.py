from django.db import models
from django.utils.translation import gettext_lazy as _


class WatchedMovie(models.Model):
    profile = models.ForeignKey("users.Profile", on_delete=models.CASCADE)
    adult = models.BooleanField(default=False)
    backdrop_path = models.CharField(max_length=255, blank=True)
    genre_ids = models.JSONField()
    original_language = models.CharField(max_length=10)
    original_title = models.CharField(max_length=510)
    overview = models.TextField()
    popularity = models.DecimalField(max_digits=10, decimal_places=3)
    poster_path = models.CharField(max_length=255, blank=True)
    release_date = models.DateField()
    title = models.CharField(max_length=510)
    video = models.BooleanField(default=False)
    vote_average = models.DecimalField(max_digits=5, decimal_places=3)
    vote_count = models.PositiveIntegerField()
    watched_at = models.DateTimeField(auto_now_add=True)
    times_watched = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = _("Movie")
        verbose_name_plural = _("Movies")
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["original_title", "release_date"],
                name="unique_original_title_release_date",
                violation_error_message=_("This movie has already been watched."),
            )
        ]

    def __str__(self):
        return f"{self.profile.user.name} watched {self.title}"
