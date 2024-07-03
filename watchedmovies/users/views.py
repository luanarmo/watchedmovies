from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from . import serializers
from .services import user_create

User = get_user_model()


class RegisterUserView(APIView):
    """Register a new user profile"""

    throttle_classes = [AnonRateThrottle]
    permission_classes = [AllowAny]

    @extend_schema(
        request=serializers.RegisterUserSerializer,
        responses={201: serializers.RegisterUserSerializer},
    )
    def post(self, request):
        """Validate data and create a new user profile"""
        serializer = serializers.RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.pop("password2")  # Remove password2 from validated data before creating the user
        user_create(**serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the current user data"""
    user = request.user
    serializer = serializers.UserSerializer(user)
    return Response(serializer.data)


@extend_schema(
    methods=["PUT", "PATCH"],
    request=serializers.UpdateUserSerializer,
    responses={200: serializers.UpdateUserSerializer},
)
@api_view(["PUT", "PATCH"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAuthenticated])
def update(request):
    """Update the current user data"""
    user = request.user
    serializer = serializers.UpdateUserSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@extend_schema(
    methods=["POST"],
    request=serializers.ChangePasswordSerializer,
    responses={200: serializers.ChangePasswordSerializer},
)
@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the current user password"""
    user = request.user
    serializer = serializers.ChangePasswordSerializer(data=request.data, context={"user": user})
    serializer.is_valid(raise_exception=True)
    user.set_password(serializer.validated_data["new_password"])
    user.save()
    return Response({"detail": _("Password changed successfully.")})


@api_view(["DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAuthenticated])
def delete(request):
    """Delete the current user account"""
    user = request.user
    user.delete()
    return Response({"detail": _("User account deleted.")})
