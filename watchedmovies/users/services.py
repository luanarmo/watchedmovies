from config.settings.base import env

from .models import Profile, User
from .utils.generate_verification_token import generate_verification_token, get_user_by_uid
from .utils.sendmail import send_email


def user_create(*, email: str, profile: dict = {}, password: str) -> User:
    """Create a new user with the given data and send a welcome email to the user."""
    profile_data = profile
    user = User(email=email, is_active=False)
    user.set_password(password)
    user.full_clean()
    user.save()
    profile = Profile(user=user, **profile_data)
    profile.full_clean()  # Validate profile data
    profile.save()

    frontend_url = env("FRONTEND_URL", default="localhost")
    uid, token = generate_verification_token(user)
    verification_url = f"{frontend_url}#/verify/{uid}/{token}/"

    send_email(
        subject="Verify your email address",
        template="email_verification.html",
        context={"url": verification_url},
        to=user.email,
    )
    return user


def send_greeting_email(*, uid: str) -> User:
    """Send a greeting email to the user with the given uid only if the user isn't active."""
    user = get_user_by_uid(uid)

    if user.is_active:
        return user

    frontend_url = env("FRONTEND_URL", default="localhost")
    home_url = f"{frontend_url}#/"
    send_email(
        subject="Welcome to WatchedMovies",
        template="successful_registration.html",
        context={"email": user.email, "url": home_url},
        to=user.email,
    )
    return user


def change_password(*, uid: str, new_password: str) -> User:
    """Change the password of the user with the given email."""
    user = get_user_by_uid(uid)
    user.set_password(new_password)
    user.full_clean()
    user.save()
    return user


def user_update(*, user: User, name: str = None, profile: dict = None) -> User:
    """Update the user data with the given data."""
    # Update user data if provided
    user.name = name or user.name
    user.full_clean()
    user.save()
    # Update profile data if provided
    if profile:
        [setattr(user.profile, key, value) for key, value in profile.items()]
        user.profile.full_clean()
        user.profile.save()

    return user


def send_password_reset_email(*, email: str) -> None:
    """Send a reset password email to the user with the given email."""
    user = User.objects.get(email=email)

    frontend_url = env("FRONTEND_URL", default="localhost")
    uid, token = generate_verification_token(user)
    reset_password_url = f"{frontend_url}#/resetPassword/{uid}/{token}/"

    send_email(
        subject="Reset your password",
        template="reset_password.html",
        context={"url": reset_password_url},
        to=user.email,
    )
