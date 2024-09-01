from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import GenericViewSet

from . import serializers, services

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
            "change_password": serializers.ChangePasswordSerializer,
        }
        return actions.get(self.action, serializers.DefaultSerializer)

    def create(self, request, *args, **kwargs):
        """Validate data and create a new user profile"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.pop("confirm_password")
        services.user_create(**serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["put"], url_path="change_password", url_name="change_password")
    @extend_schema(request=serializers.ChangePasswordSerializer, methods=["PUT"])
    def change_password(self, request, *args, **kwargs):
        """Change the password of the user with the given email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        services.change_password(email=data["email"], new_password=data["new_password"])
        return Response({"detail": "Password changed successfully."})


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
