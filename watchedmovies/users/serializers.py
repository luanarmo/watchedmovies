from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Profile

User = get_user_model()


class DefaultSerializer(serializers.Serializer):
    """Default serializer to handle empty requests"""

    pass


class ProfileSerializer(serializers.ModelSerializer[Profile]):
    """Profile serializer to display user profile information"""

    bio = serializers.CharField(required=False)
    birth_date = serializers.DateField(required=False)

    def validate_birth_date(self, value):
        # No future birth dates allowed
        if value and value > value.today():
            raise serializers.ValidationError("Invalid date - future dates are not allowed.")
        return value

    class Meta:
        model = Profile
        fields = ("pk", "bio", "birth_date")


class RegisterUserSerializer(serializers.Serializer):
    """User serializer to register a new user"""

    name = serializers.CharField(required=False, max_length=255)
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Email already exists.",
            )
        ],
    )
    profile = ProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField()

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """User serializer to display user information"""

    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ("pk", "name", "email", "profile")


class UpdateUserSerializer(serializers.ModelSerializer):
    """User serializer to update user information"""

    profile = ProfileSerializer()
    email = serializers.CharField(read_only=True)
    pk = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ("profile", "name", "email", "pk")


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer to reset user password"""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer to change user password"""

    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs
