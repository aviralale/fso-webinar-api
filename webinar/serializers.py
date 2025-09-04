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
            "image",
            "start_time",
            "duration_minutes",
            "capacity",
            "price",
            "host_name",
            "registered_count",
            "is_full",
        ]


class RegistrationSerializer(serializers.ModelSerializer):
    webinar_title = serializers.CharField(source="webinar.title", read_only=True)
    webinar_start_time = serializers.DateTimeField(
        source="webinar.start_time", read_only=True
    )
    webinar_price = serializers.DecimalField(
        source="webinar.price", max_digits=10, decimal_places=2, read_only=True
    )

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
        ]
        read_only_fields = [
            "id",
            "payment_status",
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature",
            "registered_at",
        ]


class PaymentVerificationSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
    registration_id = serializers.IntegerField()
