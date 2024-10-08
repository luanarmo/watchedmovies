from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from watchedmovies.users.managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for watchedmovies.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    fields: name, email, email_verified
    """

    # First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = models.EmailField(_("email address"), unique=True)
    username = None  # type: ignore
    email_verified = models.BooleanField(_("email verified"), default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        """Return user email as string representation."""
        return self.email


class Profile(models.Model):
    """
    Profile model for the user.
    fields: user, bio, birth_date
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)

    class Meta:
        managed = True
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["id"]

    def __str__(self):
        """Return user email as string representation."""
        return self.user.email
