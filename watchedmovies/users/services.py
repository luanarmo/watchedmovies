from django.db import transaction

from .models import Profile, User
from .utils.sendmail import send_emails


@transaction.atomic
def user_create(*, name: str, email: str, profile: any, password: str) -> User:
    """Create a new user with the given data and send a welcome email to the user."""
    profile_data = profile
    user = User(name=name, email=email)
    user.set_password(password)
    user.full_clean()
    user.save()
    profile = Profile(user=user, **profile_data)
    profile.full_clean()  # Validate profile data
    profile.save()
    send_emails(name=name, email=email)
    return user
