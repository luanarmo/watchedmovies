from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Profile
from .models import User as UserType

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer[Profile]):
    bio = serializers.CharField(required=False)
    birth_date = serializers.DateField(required=False)

    class Meta:
        model = Profile
        fields = ("pk", "bio", "birth_date")


class RegisterUserSerializer(serializers.ModelSerializer[UserType]):
    """User serializer to register a new user"""

    name = serializers.CharField(required=False, max_length=255)
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=_("Email already exists."),
            )
        ],
    )
    profile = ProfileSerializer()
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("pk", "name", "email", "profile", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": _("Passwords do not match.")})
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

    class Meta:
        model = User
        fields = ("profile", "name")

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile")
        profile = instance.profile
        instance.name = validated_data.get("name", instance.name)
        instance.full_clean()
        instance.save()

        profile.bio = profile_data.get("bio", profile.bio)
        profile.birth_date = profile_data.get("birth_date", profile.birth_date)
        profile.full_clean()
        profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer to change user password"""

    model = User
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})

        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError({"new_password": _("New password must be different from old password.")})

        return data

    def validate_old_password(self, value):
        user = self.context["user"]
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": _("Old password is incorrect.")})
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.full_clean()
        instance.save()
        return instance
