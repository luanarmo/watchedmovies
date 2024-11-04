from .models import Profile, User


def user_create(*, email: str, profile: dict = {}, password: str) -> User:
    """Create a new user with the given data and send a welcome email to the user."""
    profile_data = profile
    user = User(email=email)
    user.set_password(password)
    user.full_clean()
    user.save()
    profile = Profile(user=user, **profile_data)
    profile.full_clean()  # Validate profile data
    profile.save()
    return user


def change_password(*, email: str, new_password: str) -> User:
    """Change the password of the user with the given email."""
    user = User.objects.get(email=email)
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
