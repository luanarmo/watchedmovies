from .models import Profile, User
from .utils.sendmail import send_emails


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


def change_password(*, email: str, new_password: str) -> User:
    """Change the password of the user with the given email."""
    user = User.objects.get(email=email)
    user.set_password(new_password)
    user.full_clean()
    user.save()
    return user
