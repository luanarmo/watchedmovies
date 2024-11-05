from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from watchedmovies.users.models import User


def generate_verification_token(user: User) -> tuple:
    """
    Generate a verification token for the given user.
    """
    uid = urlsafe_base64_encode(str(user.pk).encode("utf-8"))
    token = default_token_generator.make_token(user)
    return uid, token


def validate_verification_token(uidb64: str, token: str) -> bool:
    """
    Validate the given verification token for the given user.
    """
    user = get_user_by_uid(uidb64)
    return default_token_generator.check_token(user, token)


def get_user_by_uid(uidb64: str) -> User:
    """
    Get the user with the given uid.
    """
    uid = urlsafe_base64_decode(uidb64).decode("utf-8")
    return User.objects.filter(pk=uid).first()
