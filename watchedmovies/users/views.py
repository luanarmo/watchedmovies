from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from . import serializers, services
from .utils.generate_verification_token import validate_verification_token
from .utils.validate_recaptcha import validate_recaptcha

User = get_user_model()


class AnonymousUserViewset(CreateModelMixin, GenericViewSet):
    """
    Create a new user profile and change the password of the user with the given email.
    """

    throttle_classes = [AnonRateThrottle]
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        actions = {
            "create": serializers.RegisterUserSerializer,
            "send_password_reset_email": serializers.ResetPasswordSerializer,
        }
        return actions.get(self.action, serializers.DefaultSerializer)

    def create(self, request, *args, **kwargs):
        """Validate data and create a new user profile"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.pop("confirm_password")
        token = serializer.validated_data.get("token")
        serializer.validated_data.pop("token")
        if not token:
            raise ValidationError({"token": ["This field is required."]})
        if not validate_recaptcha(token):
            raise ValidationError({"token": ["Invalid recaptcha token."]})

        services.user_create(**serializer.validated_data)
        return Response(
            {"detail": "User created successfully."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_name="send_password_reset_email", url_path="send_password_reset_email")
    def send_password_reset_email(self, request, *args, **kwargs):
        """Send a password reset email to the user with the given email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        services.send_password_reset_email(email=email)
        return Response({"detail": "Password reset email sent successfully."})


class UserViewSet(GenericViewSet):
    """
    Manage the current user profile.
    """

    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        actions = {
            "me": serializers.UserSerializer,
            "update_user": serializers.UpdateUserSerializer,
            "partial_update_user": serializers.UpdateUserSerializer,
        }
        return actions.get(self.action, serializers.DefaultSerializer)

    @action(detail=False, methods=["get"], url_path="me", url_name="me")
    def me(self, request, *args, **kwargs):
        """Retrieve the current user data"""
        user = self.get_object()
        serializer = serializers.UserSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=["put"], url_path="update_user", url_name="update_user")
    def update_user(self, request, *args, **kwargs):
        """Update the current user data"""
        user = self.get_object()
        serializer = serializers.UpdateUserSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        services.user_update(user=user, name=data["name"], profile=data["profile"])
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], url_path="partial_update_user", url_name="partial_update_user")
    def partial_update_user(self, request, *args, **kwargs):
        """Update the current user data"""
        user = self.get_object()
        serializer = serializers.UpdateUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        services.user_update(user=user, name=data.get("name"), profile=data.get("profile"))
        return Response(serializer.data)

    @action(detail=False, methods=["delete"], url_path="delete_user", url_name="delete_user")
    def delete_user(self, request, *args, **kwargs):
        """Delete the current user"""
        user = self.get_object()
        user.delete()
        return Response({"detail": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        if not token:
            raise ValidationError({"token": ["This field is required."]})
        if not validate_recaptcha(token):
            raise ValidationError({"token": ["Invalid recaptcha token."]})

        return super().post(request, *args, **kwargs)


class VerifyEmailTokenView(GenericAPIView):
    """
    Verify the email token and activate the user account.
    """

    permission_classes = [AllowAny]

    def get(self, request, uid, token):
        """
        Verify the email token and activate the user account
        """

        if not validate_verification_token(uid, token):
            raise ValidationError({"detail": "Invalid verification token."})

        user = services.send_greeting_email(uid=uid)

        if not user.is_active:
            user.is_active = True
            user.save()

        return Response({"detail": "Email verified successfully."})


class VerifyResetPasswordTokenView(GenericAPIView):
    """
    Verify the reset password token and activate the user account.
    """

    serializer_class = serializers.ChangePasswordSerializer

    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        """
        Verify the reset password token and activate the user account
        """

        password = request.data.get("new_password")

        if not validate_verification_token(uid, token):
            raise ValidationError({"detail": "Invalid verification token."})

        services.change_password(uid=uid, new_password=password)
        return Response({"detail": "Password changed successfully."})
