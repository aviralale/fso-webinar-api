from rest_framework import serializers
from .models import Webinar, Registration
from django.utils import timezone


class WebinarSerializer(serializers.ModelSerializer):
    host_name = serializers.CharField(source="host.get_full_name", read_only=True)
    registered_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()

    class Meta:
        model = Webinar
        fields = [
            "id",
            "title",
            "description",
            "image",
            "start_time",
            "duration_minutes",
            "capacity",
            "price",
            "host",
            "host_name",
            "registered_count",
            "is_full",
            "link",
            "platform",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_start_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Start time must be in the future.")
        return value

    def validate_host(self, value):
        if value.role != "host":
            raise serializers.ValidationError("Host must have 'host' role.")
        return value


class WebinarListSerializer(serializers.ModelSerializer):
    host_name = serializers.CharField(source="host.get_full_name", read_only=True)
    registered_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()

    class Meta:
        model = Webinar
        fields = [
            "id",
            "title",
            "description",  # Include description for better listing
            "image",
            "start_time",
            "duration_minutes",
            "capacity",
            "price",
            "host_name",
            "registered_count",
            "is_full",
            "platform",
        ]


class RegistrationSerializer(serializers.ModelSerializer):
    webinar_title = serializers.CharField(source="webinar.title", read_only=True)
    webinar_start_time = serializers.DateTimeField(
        source="webinar.start_time", read_only=True
    )
    webinar_price = serializers.DecimalField(
        source="webinar.price", max_digits=10, decimal_places=2, read_only=True
    )
    attendee_name = serializers.ReadOnlyField()
    attendee_email = serializers.ReadOnlyField()

    class Meta:
        model = Registration
        fields = [
            "id",
            "webinar",
            "webinar_title",
            "webinar_start_time",
            "webinar_price",
            "payment_status",
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature",
            "registered_at",
            "attendee_name",
            "attendee_email",
            "guest_phone",
        ]
        read_only_fields = [
            "id",
            "payment_status",
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature",
            "registered_at",
            "attendee_name",
            "attendee_email",
        ]


class AnonymousRegistrationSerializer(serializers.Serializer):
    """
    Serializer for anonymous user registration
    """

    webinar_id = serializers.IntegerField()
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_email(self, value):
        """Ensure email is valid"""
        return value.lower()

    def validate_name(self, value):
        """Ensure name is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()


class PaymentVerificationSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
    registration_id = serializers.IntegerField()


class GuestRegistrationStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for checking registration status without authentication
    """

    webinar_title = serializers.CharField(source="webinar.title", read_only=True)
    webinar_start_time = serializers.DateTimeField(
        source="webinar.start_time", read_only=True
    )
    webinar_link = serializers.SerializerMethodField()
    attendee_name = serializers.ReadOnlyField()

    class Meta:
        model = Registration
        fields = [
            "id",
            "webinar_title",
            "webinar_start_time",
            "webinar_link",
            "payment_status",
            "attendee_name",
            "registered_at",
        ]

    def get_webinar_link(self, obj):
        """Only show webinar link if payment is successful"""
        if obj.payment_status == "success":
            return obj.webinar.link
        return None
