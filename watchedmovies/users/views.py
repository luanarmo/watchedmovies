from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import GenericViewSet

from . import serializers, services

User = get_user_model()


class AnonymousUserViewset(CreateModelMixin, GenericViewSet):
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


class UserViewSet(GenericViewSet, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin):
    """Retrieve the current user data"""

    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        actions = {
            "retrieve": serializers.UserSerializer,
            "update": serializers.UpdateUserSerializer,
            "partial_update": serializers.UpdateUserSerializer,
        }
        return actions.get(self.action, serializers.DefaultSerializer)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve the current user data"""
        user = self.get_object()
        serializer = serializers.UserSerializer(user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update the current user data"""
        user = self.get_object()
        serializer = serializers.UpdateUserSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        services.user_update(user=user, name=data["name"], profile=data["profile"])
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Update the current user data"""
        user = self.get_object()
        serializer = serializers.UpdateUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        services.user_update(user=user, name=data.get("name"), profile=data.get("profile"))
        return Response(serializer.data)
