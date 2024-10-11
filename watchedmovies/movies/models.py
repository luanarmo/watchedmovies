from django.db import models


class WatchedMovie(models.Model):
    """Model that represents a watched movie."""

    adult = models.BooleanField(default=False)
    backdrop_path = models.CharField(max_length=255, blank=True)
    genre_ids = models.JSONField(blank=True, null=True)
    original_language = models.CharField(max_length=10)
    original_title = models.CharField(max_length=510)
    overview = models.TextField(blank=True)
    popularity = models.DecimalField(max_digits=10, decimal_places=3)
    poster_path = models.CharField(max_length=255, blank=True)
    release_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=510)
    video = models.BooleanField(default=False)
    vote_average = models.DecimalField(max_digits=5, decimal_places=3)
    vote_count = models.PositiveIntegerField()
    runtime = models.PositiveIntegerField(null=True, blank=True)
    more_details = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Movie"
        verbose_name_plural = "Movies"
        ordering = ["id"]

    def __str__(self):
        return self.title


class ViewDetails(models.Model):
    """Model that represents the details of a watched movie."""

    PLACE_CHOICES = [
        ("cinema", "Movie Theater"),
        ("home", "Home"),
        ("friend", "Friend's House"),
        ("other", "Other"),
    ]

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German"),
        ("it", "Italian"),
        ("pt", "Portuguese"),
        ("ru", "Russian"),
        ("ja", "Japanese"),
        ("zh", "Chinese"),
        ("ko", "Korean"),
        ("ar", "Arabic"),
        ("hi", "Hindi"),
        ("other", "Other"),
    ]

    watched_movie = models.ForeignKey(WatchedMovie, on_delete=models.CASCADE, related_name="view_details")
    profile = models.ForeignKey("users.Profile", on_delete=models.CASCADE, related_name="view_details")
    watched_at = models.DateTimeField(auto_now_add=True)
    rating = models.PositiveIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="en")
    place = models.CharField(max_length=255, choices=PLACE_CHOICES, default="home")

    class Meta:
        verbose_name = "View Details"
        verbose_name_plural = "View Details"
        ordering = ["-watched_at"]

    def __str__(self):
        return f"{self.profile.user.name} watched {self.watched_movie.title}"
