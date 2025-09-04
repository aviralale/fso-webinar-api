from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Custom Djoser user creation serializer with role field
    """

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "password",
        ]

    def validate_role(self, value):
        # Only allow attendee and host roles during registration
        # Admin users should be created via Django admin
        if value not in ["attendee", "host"]:
            raise serializers.ValidationError(
                "Only 'attendee' and 'host' roles are allowed during registration."
            )
        return value


class CustomUserSerializer(DjoserUserSerializer):
    """
    Custom Djoser user serializer with role field
    """

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for internal use
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "full_name",
        ]
        read_only_fields = ["id"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
